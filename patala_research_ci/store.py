from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ledger import Ledger
from .model import Snapshot, TrackedAnalysis, TrackedClaim


class Workspace:
    def __init__(self, root: str | Path = ".patala-ci"):
        self.root = Path(root)
        for d in ("analyses", "snapshots", "claims", "diffs", "impacts", "obligations", "plans", "receipts", "exports", "mcp_traces"):
            (self.root / d).mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(self.root / "ledger.jsonl")

    def _write(self, folder: str, key: str, obj: Any) -> Path:
        path = self.root / folder / f"{_safe(key)}.json"
        data = obj.to_dict() if hasattr(obj, "to_dict") else obj
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return path

    def _read(self, folder: str, key: str) -> dict[str, Any]:
        path = self.root / folder / f"{_safe(key)}.json"
        if not path.exists():
            raise KeyError(key)
        return json.loads(path.read_text(encoding="utf-8"))

    def save_analysis(self, obj: TrackedAnalysis) -> Path:
        return self._write("analyses", obj.analysis_id, obj)

    def load_analysis(self, analysis_id: str) -> TrackedAnalysis:
        return TrackedAnalysis.from_dict(self._read("analyses", analysis_id))

    def list_analyses(self) -> list[dict[str, Any]]:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.root / "analyses").glob("*.json"))]

    def save_snapshot(self, obj: Snapshot) -> Path:
        return self._write("snapshots", obj.snapshot_id, obj)

    def load_snapshot(self, snapshot_id: str) -> Snapshot:
        return Snapshot.from_dict(self._read("snapshots", snapshot_id))

    def save_claim(self, obj: TrackedClaim) -> Path:
        return self._write("claims", obj.claim_id, obj)

    def load_claim(self, claim_id: str) -> TrackedClaim:
        return TrackedClaim.from_dict(self._read("claims", claim_id))

    def claims_for(self, analysis: TrackedAnalysis) -> list[TrackedClaim]:
        return [self.load_claim(cid) for cid in analysis.claims]

    def save_diff(self, obj) -> Path:
        return self._write("diffs", obj.diff_id, obj)

    def save_impact(self, obj) -> Path:
        return self._write("impacts", obj.impact_id, obj)

    def save_obligation(self, obj) -> Path:
        return self._write("obligations", obj.obligation_id, obj)

    def list_obligations(self) -> list[dict[str, Any]]:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.root / "obligations").glob("*.json"))]

    def save_plan(self, plan, plan_hash: str) -> Path:
        data = plan.to_dict()
        data["plan_hash"] = plan_hash
        return self._write("plans", plan.plan_id, data)

    def save_receipt(self, receipt) -> Path:
        return self._write("receipts", receipt.receipt_id, receipt)

    def save_mcp_trace(self, trace) -> Path:
        data = trace.to_dict() if hasattr(trace, "to_dict") else trace
        trace_id = data["trace_id"]
        data = dict(data)
        if hasattr(trace, "digest"):
            data["trace_digest"] = trace.digest
        return self._write("mcp_traces", trace_id, data)

    def load_mcp_trace(self, trace_id: str) -> dict[str, Any]:
        return self._read("mcp_traces", trace_id)

    def list_mcp_traces(self) -> list[dict[str, Any]]:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.root / "mcp_traces").glob("*.json"))]

    def bind_mcp_trace(self, analysis_id: str, trace_id: str) -> dict[str, Any]:
        analysis = self.load_analysis(analysis_id)
        trace = self.load_mcp_trace(trace_id)
        event = self.ledger.append("analysis.mcp_bound", analysis_id, {
            "trace_id": trace_id,
            "trace_digest": trace.get("trace_digest"),
            "provider": trace.get("provider"),
            "connector": trace.get("connector"),
            "synthetic": bool(trace.get("synthetic", False)),
        })
        return event


def _safe(key: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in key)
