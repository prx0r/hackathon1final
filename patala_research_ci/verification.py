from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .canonical import digest_json
from .computation import evaluate_claim
from .model import ResolutionCheck, ResolutionPlan, Snapshot, TrackedClaim, VerificationReceipt
from .snapshot import utc_now


def plan_hash(plan: ResolutionPlan) -> str:
    return digest_json(plan.to_dict())


def build_resolution_plan(obligation: dict[str, Any], analysis_id: str, claim: TrackedClaim,
                          old_snapshot: Snapshot, new_snapshot: Snapshot) -> ResolutionPlan:
    binding = {
        "analysis_id": analysis_id,
        "claim_id": claim.claim_id,
        "old_snapshot_digest": old_snapshot.digest,
        "new_snapshot_digest": new_snapshot.digest,
        "claim_dependency_digest": digest_json([d.to_dict() for d in claim.dependencies]),
        "claim_computation_digest": digest_json(claim.computation or {}),
    }
    checks = [ResolutionCheck("source-health", "source_status_ok", {"expected": "OK"})]
    if claim.computation:
        checks.append(ResolutionCheck("recompute", "recompute_claim", {}))
    else:
        checks.append(ResolutionCheck("human-evidence", "evidence_artifact", {"required_keys": ["decision", "reason"]}))
    return ResolutionPlan(
        plan_id="plan:" + uuid.uuid4().hex[:14],
        version="1",
        obligation_id=obligation["obligation_id"],
        subject_binding=binding,
        checks=tuple(checks),
    )


class VerificationService:
    """QDW-inspired frozen-plan verifier for scholarly proof obligations."""

    def run(self, plan: ResolutionPlan, claim: TrackedClaim, snapshot: Snapshot,
            *, evidence_path: str | Path | None = None) -> VerificationReceipt:
        started = utc_now()
        t0 = time.monotonic()
        checks: list[dict[str, Any]] = []
        artifacts: list[dict[str, Any]] = []
        failed = False

        for check in plan.checks:
            result = {"check_id": check.check_id, "type": check.check_type, "required": check.required}
            if check.check_type == "source_status_ok":
                expected = check.params.get("expected", "OK")
                ok = snapshot.source_status == expected
                result.update({"status": "PASS" if ok else "FAIL", "observed": snapshot.source_status, "expected": expected})
            elif check.check_type == "recompute_claim":
                evaluation = evaluate_claim(claim, snapshot)
                ok = bool(evaluation.get("computable"))
                result.update({"status": "PASS" if ok else "FAIL", "evaluation": evaluation})
            elif check.check_type == "evidence_artifact":
                ok = False
                detail: dict[str, Any] = {}
                if evidence_path:
                    p = Path(evidence_path)
                    if p.exists() and p.is_file():
                        data = json.loads(p.read_text(encoding="utf-8"))
                        required = check.params.get("required_keys", [])
                        ok = all(k in data and data[k] not in (None, "") for k in required)
                        raw = p.read_bytes()
                        artifact = {"path": str(p.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                        artifacts.append(artifact)
                        detail = {"required_keys": required, "present": sorted(data.keys())}
                result.update({"status": "PASS" if ok else "FAIL", **detail})
            else:
                ok = False
                result.update({"status": "FAIL", "reason": "unknown check type"})
            if check.required and result["status"] != "PASS":
                failed = True
            checks.append(result)

        finished = utc_now()
        status = "FAIL" if failed else "PASS"
        env = {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pid": os.getpid(),
            "duration_ms": int((time.monotonic() - t0) * 1000),
        }
        body = {
            "receipt_id": "receipt:" + uuid.uuid4().hex[:14],
            "obligation_id": plan.obligation_id,
            "plan_hash": plan_hash(plan),
            "subject_binding": plan.subject_binding,
            "checks": checks,
            "artifacts": artifacts,
            "started_at": started,
            "finished_at": finished,
            "status": status,
            "environment": env,
        }
        rh = digest_json(body)
        return VerificationReceipt(**body, receipt_hash=rh)

    @staticmethod
    def verify_receipt(receipt: VerificationReceipt, plan: ResolutionPlan) -> tuple[bool, str]:
        if receipt.plan_hash != plan_hash(plan):
            return False, "plan_hash"
        if receipt.subject_binding != plan.subject_binding:
            return False, "subject_binding"
        body = receipt.to_dict()
        stored = body.pop("receipt_hash")
        if digest_json(body) != stored:
            return False, "receipt_hash"
        if receipt.status != "PASS":
            return False, "run_status"
        if any(x.get("required") and x.get("status") != "PASS" for x in receipt.checks):
            return False, "required_check"
        for art in receipt.artifacts:
            p = Path(art["path"])
            if not p.exists():
                return False, "artifact_missing"
            raw = p.read_bytes()
            if len(raw) != art["bytes"] or hashlib.sha256(raw).hexdigest() != art["sha256"]:
                return False, "artifact_hash"
        return True, "ok"
