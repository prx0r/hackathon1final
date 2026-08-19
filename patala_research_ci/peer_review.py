from __future__ import annotations

"""Evidence-first peer-review primitives over the continuity kernel.

The module follows the FactReview/RevCI direction: reviews are structured findings with
claim/evidence links and explicit contradictions, not one opaque prose score. It does not
make autonomous scientific acceptance decisions.
"""

from dataclasses import dataclass, field, asdict
from typing import Any
import uuid

from .canonical import digest_json
from .adjudication import EvidenceItem, EvidencePacket, make_packet


@dataclass(frozen=True)
class ReviewEvidenceSpan:
    ref: str
    relation: str  # supports | contradicts | contextualizes | unavailable
    excerpt_digest: str | None = None
    location: dict[str, Any] = field(default_factory=dict)
    notes: str = ""


@dataclass(frozen=True)
class ReviewFinding:
    finding_id: str
    claim_id: str
    status: str  # SUPPORTED | CONTRADICTED | INSUFFICIENT | NEEDS_HUMAN_REVIEW
    rationale: str
    evidence: tuple[ReviewEvidenceSpan, ...] = ()
    checks: tuple[dict[str, Any], ...] = ()
    authority: str = "machine_proposed"

    @property
    def digest(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence"] = [asdict(x) for x in self.evidence]
        d["checks"] = list(self.checks)
        return d


@dataclass(frozen=True)
class ReviewBundle:
    review_id: str
    subject_id: str
    findings: tuple[ReviewFinding, ...]
    reviewer: str = "patala"
    authority: str = "machine_proposed"

    @property
    def digest(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "subject_id": self.subject_id,
            "findings": [x.to_dict() for x in self.findings],
            "reviewer": self.reviewer,
            "authority": self.authority,
        }


def make_finding(claim_id: str, status: str, rationale: str,
                 evidence: list[ReviewEvidenceSpan] | None = None,
                 checks: list[dict[str, Any]] | None = None) -> ReviewFinding:
    return ReviewFinding(
        finding_id="finding:" + uuid.uuid4().hex[:16],
        claim_id=claim_id,
        status=status,
        rationale=rationale,
        evidence=tuple(evidence or []),
        checks=tuple(checks or []),
    )


def make_review(subject_id: str, findings: list[ReviewFinding], reviewer: str = "patala") -> ReviewBundle:
    return ReviewBundle("review:" + uuid.uuid4().hex[:16], subject_id, tuple(findings), reviewer)


def finding_to_evidence_packet(finding: ReviewFinding, expertise: list[str] | None = None) -> EvidencePacket:
    """Promote an unresolved finding into a human-resolution packet."""
    evidence = [EvidenceItem(x.ref, x.excerpt_digest or digest_json(x.location), x.relation, x.notes) for x in finding.evidence]
    return make_packet(
        question=f"Resolve peer-review finding {finding.finding_id} for claim {finding.claim_id}: {finding.rationale}",
        evidence=evidence,
        expertise=expertise,
        acceptance={
            "finding_digest": finding.digest,
            "required": ["decision", "reason"],
            "allowed_decisions": ["ACCEPT_SUPPORT", "REJECT_SUPPORT", "REVISE_CLAIM", "INSUFFICIENT_EVIDENCE"],
        },
    )
