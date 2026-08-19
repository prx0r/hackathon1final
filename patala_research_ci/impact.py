from __future__ import annotations

from collections import Counter
import uuid

from .learning import wilson_lower
from .model import (
    ClaimImpact, ClaimState, Dependency, ImpactReport, Materiality,
    SemanticDiff, Severity, TrackedClaim
)


def _relation_matches(dep: Dependency, rel: dict) -> bool:
    return (
        (dep.source is None or dep.source == rel.get("source"))
        and (dep.relation is None or dep.relation == rel.get("relation"))
        and (dep.target is None or dep.target == rel.get("target"))
    )


def _change_hits_dependency(change, dep: Dependency) -> bool:
    if change.kind == "SOURCE_PARTIAL":
        return dep.kind == "relation"
    if dep.kind == "query_membership":
        return change.kind in {"ENTITY_ADDED", "ENTITY_REMOVED"}
    if dep.kind == "entity":
        return change.entity_id == dep.entity_id and change.kind in {
            "ENTITY_REMOVED", "FIELD_CHANGED", "RAW_RECORD_CHANGED"
        }
    if dep.kind == "field":
        return change.entity_id == dep.entity_id and change.kind == "FIELD_CHANGED" and (
            dep.field_path == change.path or (dep.field_path and change.path and change.path.startswith(dep.field_path + "."))
        )
    if dep.kind == "relation" and change.relation:
        return change.kind in {"RELATION_ADDED", "RELATION_REMOVED"} and _relation_matches(dep, change.relation)
    return False


def _state_for_changes(changes) -> str:
    mats = {c.materiality for c in changes}
    kinds = {c.kind for c in changes}
    if Materiality.SOURCE_HEALTH.value in mats:
        return ClaimState.BLOCKED.value
    if Materiality.RETRACTION.value in mats or Materiality.CORRECTION.value in mats:
        return ClaimState.HUMAN_REVIEW_REQUIRED.value
    if "RELATION_REMOVED" in kinds or "ENTITY_REMOVED" in kinds:
        return ClaimState.RECOMPUTE_REQUIRED.value
    if Materiality.QUERY_MEMBERSHIP.value in mats or Materiality.RELATION.value in mats:
        return ClaimState.RECOMPUTE_REQUIRED.value
    return ClaimState.SOURCE_CHANGED.value


def _compute_severity(changes, claim) -> str:
    """Compute severity based on change types and claim properties."""
    kinds = {c.kind for c in changes}
    mats = {c.materiality for c in changes}

    if Materiality.RETRACTION.value in mats or Materiality.CORRECTION.value in mats:
        return Severity.CRITICAL.value
    if "ENTITY_REMOVED" in kinds or "RELATION_REMOVED" in kinds:
        return Severity.HIGH.value
    if Materiality.RELATION.value in mats:
        return Severity.MEDIUM.value
    return Severity.LOW.value


def _compute_confidence(changes, claim, diff_total_changes: int) -> float:
    """Compute Wilson confidence in the impact assessment.

    More changes = less confidence (more noise). Fewer targeted changes = more confidence.
    """
    n_deps = max(len(claim.dependencies), 1)
    n_hits = len(changes)
    # Confidence: how many of the claim's dependencies were actually hit
    hit_ratio = n_hits / n_deps
    # Wilson lower bound: confidence that the claim is truly affected
    return wilson_lower(n_hits, max(n_deps, 1))


def compute_impact(analysis_id: str, diff: SemanticDiff, claims: list[TrackedClaim]) -> ImpactReport:
    impacts: list[ClaimImpact] = []
    unavailable = [c for c in diff.changes if c.kind == "SOURCE_UNAVAILABLE"]
    total_changes = len(diff.changes)

    for claim in claims:
        hit = []
        if unavailable:
            hit = unavailable
        else:
            for c in diff.changes:
                if any(_change_hits_dependency(c, dep) for dep in claim.dependencies):
                    hit.append(c)
        if not hit:
            impacts.append(ClaimImpact(claim.claim_id, ClaimState.CURRENT.value, [], []))
            continue
        state = _state_for_changes(hit)
        impacts.append(ClaimImpact(
            claim.claim_id,
            state,
            [c.change_id for c in hit],
            [c.reason for c in hit],
        ))

    summary = dict(Counter(x.state for x in impacts))
    return ImpactReport(
        impact_id="impact:" + uuid.uuid4().hex[:14],
        analysis_id=analysis_id,
        diff_id=diff.diff_id,
        claims=impacts,
        summary=summary,
    )
