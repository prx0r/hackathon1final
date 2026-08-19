"""Trace-to-dependency compiler.

The hard problem: given an MCP trace with tool calls and results,
extract which OpenAIRE observations support which downstream claims.

This is the ONE mechanism that matters. Everything else is infrastructure.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from .canonical import digest_json


@dataclass
class Observation:
    """A single upstream observation extracted from an MCP trace."""
    obs_id: str
    source: str          # "openaire", "scholexplorer", etc.
    tool: str            # tool name used
    entity_ids: list[str]  # OpenAIRE IDs returned
    request_digest: str  # hash of the request
    result_digest: str   # hash of the result
    observed_at: str
    source_status: str = "OK"

    def to_dict(self) -> dict:
        return {
            "obs_id": self.obs_id,
            "source": self.source,
            "tool": self.tool,
            "entity_ids": self.entity_ids,
            "request_digest": self.request_digest,
            "result_digest": self.result_digest,
            "observed_at": self.observed_at,
            "source_status": self.source_status,
        }


@dataclass
class CandidateDependency:
    """A proposed dependency from observation to downstream object."""
    dep_id: str
    obs_id: str
    dep_kind: str        # "entity", "field", "relation", "query_membership"
    entity_id: str | None = None
    field_path: str | None = None
    relation_type: str | None = None
    confidence: float = 0.0  # how sure we are this dependency is real
    evidence: str = ""       # why we think this dependency exists

    def to_dict(self) -> dict:
        d = {
            "dep_id": self.dep_id,
            "obs_id": self.obs_id,
            "dep_kind": self.dep_kind,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }
        if self.entity_id: d["entity_id"] = self.entity_id
        if self.field_path: d["field_path"] = self.field_path
        if self.relation_type: d["relation_type"] = self.relation_type
        return d


# ============================================================
# THE CORE: trace → observations → candidate dependencies
# ============================================================

_OPENAIRE_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+::[A-Za-z0-9_.:%+\-/=]{6,}$")
_DOI_RE = re.compile(r"10\.\d{4,}/[^\s\"]+")
_ORCID_RE = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")


def _extract_ids_from_value(value: Any) -> set[str]:
    """Extract OpenAIRE IDs, DOIs, ORCIDs from any nested structure."""
    ids = set()
    if isinstance(value, str):
        if _OPENAIRE_ID_RE.match(value):
            ids.add(value)
        for m in _DOI_RE.finditer(value):
            ids.add(m.group())
        for m in _ORCID_RE.finditer(value):
            ids.add(m.group())
    elif isinstance(value, dict):
        for v in value.values():
            ids |= _extract_ids_from_value(v)
    elif isinstance(value, list):
        for item in value:
            ids |= _extract_ids_from_value(item)
    return ids


def trace_to_observations(trace: dict) -> list[Observation]:
    """Extract observations from an MCP trace.

    Each tool call becomes one observation with all entity IDs found in the result.
    """
    observations = []
    for call in trace.get("calls", []):
        result = call.get("result", {})
        request = call.get("arguments", {})

        entity_ids = sorted(call.get("openaire_ids", []) or [])
        entity_ids += sorted(_extract_ids_from_value(result))

        obs = Observation(
            obs_id="obs:" + uuid.uuid4().hex[:12],
            source=trace.get("connector", "unknown"),
            tool=call.get("tool_name", "unknown"),
            entity_ids=entity_ids,
            request_digest=digest_json(request),
            result_digest=digest_json(result),
            observed_at=call.get("called_at", ""),
        )
        observations.append(obs)
    return observations


def observations_to_dependencies(
    observations: list[Observation],
    downstream_text: str | None = None,
) -> list[CandidateDependency]:
    """Generate candidate dependencies from observations.

    For each observation, emit entity-level dependencies for all found IDs.
    If downstream_text is provided, try to match which IDs appear in the text.
    """
    deps = []
    seen = set()

    for obs in observations:
        for eid in obs.entity_ids:
            key = (obs.obs_id, eid)
            if key in seen:
                continue
            seen.add(key)

            confidence = 0.8 if downstream_text and eid in downstream_text else 0.5

            deps.append(CandidateDependency(
                dep_id="dep:" + uuid.uuid4().hex[:12],
                obs_id=obs.obs_id,
                dep_kind="entity",
                entity_id=eid,
                confidence=confidence,
                evidence=f"extracted from {obs.tool} call result",
            ))

        # Also emit query-membership dependency for the search tool
        if "search" in obs.tool.lower() or "Search" in obs.tool:
            deps.append(CandidateDependency(
                dep_id="dep:" + uuid.uuid4().hex[:12],
                obs_id=obs.obs_id,
                dep_kind="query_membership",
                confidence=0.6,
                evidence=f"query result from {obs.tool}",
            ))

    return deps


def compile_trace(
    trace: dict,
    claim_text: str | None = None,
) -> dict:
    """Full compilation: trace → observations → dependencies.

    Returns a structured result with observations, dependencies, and statistics.
    """
    observations = trace_to_observations(trace)
    deps = observations_to_dependencies(observations, claim_text)

    total_ids = set()
    for obs in observations:
        total_ids.update(obs.entity_ids)

    return {
        "trace_id": trace.get("trace_id", "unknown"),
        "connector": trace.get("connector", "unknown"),
        "observations": [o.to_dict() for o in observations],
        "dependencies": [d.to_dict() for d in deps],
        "stats": {
            "tool_calls": len(observations),
            "unique_entity_ids": len(total_ids),
            "candidate_dependencies": len(deps),
            "high_confidence": sum(1 for d in deps if d.confidence >= 0.7),
            "low_confidence": sum(1 for d in deps if d.confidence < 0.5),
        },
    }
