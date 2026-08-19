from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .computation import evaluate_claim
from .diff import diff_snapshots
from .impact import compute_impact
from .model import ClaimState, QuerySpec, SourceStatus, TrackedAnalysis, TrackedClaim
from .obligations import obligations_from_impact
from .openaire import OpenAIREStack
from .snapshot import fetch_snapshot, utc_now
from .store import Workspace
from .verification import VerificationService, build_resolution_plan, plan_hash


class ResearchCI:
    def __init__(self, workspace: Workspace, stack: OpenAIREStack | None = None):
        self.ws = workspace
        self.stack = stack or OpenAIREStack()
        self.verifier = VerificationService()

    def track(self, analysis_id: str, title: str, query: QuerySpec,
              claims: list[TrackedClaim] | None = None, description: str = "") -> TrackedAnalysis:
        snapshot = fetch_snapshot(self.stack, query)
        # Reject failed source as baseline — cannot establish knowledge from nothing.
        if snapshot.source_status in (SourceStatus.UNAVAILABLE.value,):
            raise ValueError(
                f"Cannot track analysis: OpenAIRE source unavailable. "
                f"Cannot establish a baseline from a failed fetch. "
                f"Source error: {snapshot.source_error or 'unknown'}"
            )
        self.ws.save_snapshot(snapshot)
        claim_ids = []
        for claim in claims or []:
            if claim.computation and snapshot.source_status == SourceStatus.OK.value:
                baseline = evaluate_claim(claim, snapshot)
                claim.baseline_value = baseline.get("value")
                claim.baseline_supported = baseline.get("supported")
            self.ws.save_claim(claim)
            claim_ids.append(claim.claim_id)
        analysis = TrackedAnalysis(
            analysis_id=analysis_id, title=title, query=query, created_at=utc_now(),
            latest_snapshot_id=snapshot.snapshot_id, claims=claim_ids, description=description,
        )
        self.ws.save_analysis(analysis)
        self.ws.ledger.append("analysis.tracked", analysis_id, {
            "snapshot_id": snapshot.snapshot_id, "snapshot_digest": snapshot.digest,
            "query": query.to_dict(), "claims": claim_ids, "source_status": snapshot.source_status,
        })
        return analysis

    def track_from_snapshot(self, analysis_id: str, title: str, query: QuerySpec, snapshot,
                            claims: list[TrackedClaim] | None = None, description: str = "") -> TrackedAnalysis:
        """Offline/reproducible tracking entrypoint used by fixtures and historical imports."""
        self.ws.save_snapshot(snapshot)
        claim_ids = []
        for claim in claims or []:
            if claim.computation and snapshot.source_status == SourceStatus.OK.value:
                baseline = evaluate_claim(claim, snapshot)
                claim.baseline_value = baseline.get("value")
                claim.baseline_supported = baseline.get("supported")
            self.ws.save_claim(claim)
            claim_ids.append(claim.claim_id)
        analysis = TrackedAnalysis(
            analysis_id=analysis_id, title=title, query=query, created_at=utc_now(),
            latest_snapshot_id=snapshot.snapshot_id, claims=claim_ids, description=description,
        )
        self.ws.save_analysis(analysis)
        self.ws.ledger.append("analysis.tracked", analysis_id, {
            "snapshot_id": snapshot.snapshot_id, "snapshot_digest": snapshot.digest,
            "query": query.to_dict(), "claims": claim_ids, "source_status": snapshot.source_status,
            "mode": "offline_snapshot",
        })
        return analysis

    def verify(self, analysis_id: str, *, supplied_snapshot=None) -> dict[str, Any]:
        analysis = self.ws.load_analysis(analysis_id)
        old = self.ws.load_snapshot(analysis.latest_snapshot_id)
        new = supplied_snapshot or fetch_snapshot(self.stack, analysis.query)
        self.ws.save_snapshot(new)
        diff = diff_snapshots(analysis_id, old, new)
        self.ws.save_diff(diff)
        claims = self.ws.claims_for(analysis)
        impact = compute_impact(analysis_id, diff, claims)
        self.ws.save_impact(impact)
        obligations = obligations_from_impact(impact)
        for ob in obligations:
            claim = next(c for c in claims if c.claim_id == ob.claim_id)
            plan = build_resolution_plan(ob.to_dict(), analysis_id, claim, old, new)
            ob.resolution_plan_hash = plan_hash(plan)
            self.ws.save_plan(plan, ob.resolution_plan_hash)
            self.ws.save_obligation(ob)
        # A failed/partial observation is evidence about source health, not a new
        # trustworthy baseline. Keep comparing future checks to the last known-good state.
        if new.source_status == SourceStatus.OK.value:
            analysis.latest_snapshot_id = new.snapshot_id
        self.ws.save_analysis(analysis)
        self.ws.ledger.append("analysis.verified", analysis_id, {
            "old_snapshot": old.snapshot_id, "new_snapshot": new.snapshot_id,
            "diff_id": diff.diff_id, "impact_id": impact.impact_id,
            "obligations": [o.obligation_id for o in obligations],
            "source_status": new.source_status,
        })
        return {"analysis": analysis, "old": old, "new": new, "diff": diff, "impact": impact, "obligations": obligations}

    def resolve_computable(self, obligation_id: str) -> dict[str, Any]:
        ob = self.ws._read("obligations", obligation_id)
        analysis = self.ws.load_analysis(ob["analysis_id"])
        claim = self.ws.load_claim(ob["claim_id"])
        current = self.ws.load_snapshot(analysis.latest_snapshot_id)
        plan_data = None
        for p in (self.ws.root / "plans").glob("*.json"):
            data = __import__("json").loads(p.read_text(encoding="utf-8"))
            if data.get("obligation_id") == obligation_id:
                plan_data = data
                break
        if not plan_data:
            raise KeyError(f"plan for {obligation_id}")
        from .model import ResolutionCheck, ResolutionPlan
        plan = ResolutionPlan(
            plan_id=plan_data["plan_id"], version=plan_data["version"], obligation_id=plan_data["obligation_id"],
            subject_binding=plan_data["subject_binding"],
            checks=tuple(ResolutionCheck(**c) for c in plan_data["checks"]),
        )
        receipt = self.verifier.run(plan, claim, current)
        self.ws.save_receipt(receipt)
        valid, reason = self.verifier.verify_receipt(receipt, plan)
        evaluation = evaluate_claim(claim, current)
        if valid and evaluation.get("computable"):
            claim.state = ClaimState.VERIFIED_CURRENT.value if evaluation.get("supported") else ClaimState.UNSUPPORTED.value
            self.ws.save_claim(claim)
            ob["status"] = "RESOLVED"
            ob["resolution_receipt_id"] = receipt.receipt_id
            ob["resolution_result"] = evaluation
            self.ws._write("obligations", obligation_id, ob)
            self.ws.ledger.append("obligation.resolved", obligation_id, {
                "claim_id": claim.claim_id, "receipt_id": receipt.receipt_id,
                "claim_state": claim.state, "evaluation": evaluation,
            })
        return {"receipt": receipt, "valid": valid, "reason": reason, "evaluation": evaluation, "claim": claim, "obligation": ob}
