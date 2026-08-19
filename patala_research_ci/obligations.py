from __future__ import annotations

import uuid

from .learning import PriorityScore
from .model import ClaimState, ImpactReport, ProofObligation, Severity


def obligations_from_impact(report: ImpactReport) -> list[ProofObligation]:
    out: list[ProofObligation] = []
    for impact in report.claims:
        if impact.state in {ClaimState.CURRENT.value, ClaimState.VERIFIED_CURRENT.value}:
            continue
        if impact.state == ClaimState.BLOCKED.value:
            action = "RETRY_SOURCE"
            severity = Severity.HIGH.value
        elif impact.state == ClaimState.HUMAN_REVIEW_REQUIRED.value:
            action = "HUMAN_REVIEW"
            severity = Severity.CRITICAL.value
        elif impact.state == ClaimState.RECOMPUTE_REQUIRED.value:
            action = "RECOMPUTE"
            severity = Severity.MEDIUM.value
        else:
            action = "RECHECK_EVIDENCE"
            severity = Severity.LOW.value

        # Compute priority from blast radius and change characteristics
        n_changes = len(impact.change_ids)
        urgency = 1.0 if severity in (Severity.CRITICAL.value, Severity.HIGH.value) else 0.5
        cost = 10.0 if action == "HUMAN_REVIEW" else 1.0

        ps = PriorityScore(
            blast_radius=n_changes,
            urgency=urgency,
            cost=cost,
            confidence=0.5,
            recency=0.5,
        )

        out.append(ProofObligation(
            obligation_id="po:" + uuid.uuid4().hex[:14],
            analysis_id=report.analysis_id,
            claim_id=impact.claim_id,
            trigger_change_ids=impact.change_ids,
            reason="; ".join(impact.reasons) or impact.state,
            action=action,
            priority=round(ps.score, 3),
            severity=severity,
            blast_radius=n_changes,
        ))

    # Sort by priority descending (highest priority first)
    out.sort(key=lambda o: -o.priority)
    return out
