from __future__ import annotations

"""Fail-closed claim/evidence binding for MCP traces.

This is a lightweight offline verifier inspired by ProvenanceGuard's source-preserving
interface. It does not reproduce its learned embedding router, NLI model or calibrator.
Instead it validates explicit source IDs, protected literals and deterministic evidence
bindings, and exposes a semantic-verifier callback for stronger deployments.
"""

from dataclasses import dataclass, asdict
from typing import Any, Callable
import json
import re
import uuid

from .canonical import digest_json
from .mcp_trace import MCPTrace

_PROTECTED = re.compile(r"(?<!\w)(?:\d+(?:\.\d+)?%?|10\.\d{4,9}/[-._;()/:A-Za-z0-9]+|[A-Za-z0-9_.-]+::[A-Za-z0-9_.:%+\-/=]{6,})(?!\w)")


@dataclass(frozen=True)
class EvidenceBinding:
    binding_id: str
    claim_id: str
    trace_id: str
    call_indexes: tuple[int, ...]
    openaire_ids: tuple[str, ...]
    authority: str = "machine_proposed"
    confidence: float = 1.0

    @property
    def digest(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SupportVerdict:
    claim_id: str
    status: str  # SUPPORTED | BLOCKED | UNAVAILABLE
    reasons: tuple[str, ...]
    binding_digest: str

    def to_dict(self):
        return asdict(self)


def candidate_bindings_from_trace(claim_id: str, trace: MCPTrace, select_ids: list[str] | None = None) -> EvidenceBinding:
    selected = set(select_ids or trace.openaire_ids)
    indexes = []
    observed: set[str] = set()
    for i, call in enumerate(trace.calls):
        ids = set(call.openaire_ids)
        if ids & selected:
            indexes.append(i); observed.update(ids & selected)
    if selected and observed != selected:
        missing = sorted(selected - observed)
        raise ValueError(f"selected IDs not present in MCP trace: {missing}")
    return EvidenceBinding(
        "binding:" + uuid.uuid4().hex[:16], claim_id, trace.trace_id,
        tuple(indexes), tuple(sorted(observed)), "machine_proposed", 1.0,
    )


def verify_binding(claim_id: str, claim_text: str, trace: MCPTrace, binding: EvidenceBinding,
                   semantic_verifier: Callable[[str, list[Any]], bool | None] | None = None) -> SupportVerdict:
    reasons: list[str] = []
    if binding.claim_id != claim_id or binding.trace_id != trace.trace_id:
        reasons.append("binding subject mismatch")
    if not binding.call_indexes:
        reasons.append("no source-specific MCP calls bound")
    evidence = []
    ids: set[str] = set()
    for idx in binding.call_indexes:
        if not 0 <= idx < len(trace.calls):
            reasons.append(f"call index out of range: {idx}")
            continue
        call = trace.calls[idx]
        evidence.append(call.result)
        ids.update(call.openaire_ids)
    for oid in binding.openaire_ids:
        if oid not in ids:
            reasons.append(f"OpenAIRE ID not present in selected evidence: {oid}")
    evidence_text = json.dumps(evidence, ensure_ascii=False, sort_keys=True).lower()
    protected = sorted(set(x.rstrip(".,;:)") for x in _PROTECTED.findall(claim_text)))
    # DOIs/IDs/numbers explicitly asserted by the claim must be present in the selected evidence.
    for literal in protected:
        if literal.lower() not in evidence_text:
            reasons.append(f"protected literal not grounded: {literal}")
    if semantic_verifier is not None and not reasons:
        sem = semantic_verifier(claim_text, evidence)
        if sem is False:
            reasons.append("semantic verifier rejected support")
        elif sem is None:
            return SupportVerdict(claim_id, "UNAVAILABLE", ("semantic verifier unavailable",), binding.digest)
    status = "BLOCKED" if reasons else "SUPPORTED"
    return SupportVerdict(claim_id, status, tuple(reasons), binding.digest)
