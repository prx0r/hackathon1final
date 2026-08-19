from __future__ import annotations

"""Human-resolution primitives shared by peer review, cruxes and scholar tasks."""

from dataclasses import dataclass, field, asdict
from typing import Any
import uuid

from .canonical import digest_json


@dataclass(frozen=True)
class EvidenceItem:
    ref: str
    digest: str
    role: str = "support"
    description: str = ""


@dataclass(frozen=True)
class EvidencePacket:
    packet_id: str
    question: str
    evidence: tuple[EvidenceItem, ...]
    required_expertise: tuple[str, ...] = ()
    acceptance: dict[str, Any] = field(default_factory=dict)

    @property
    def digest(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self):
        return {
            "packet_id": self.packet_id,
            "question": self.question,
            "evidence": [asdict(x) for x in self.evidence],
            "required_expertise": list(self.required_expertise),
            "acceptance": self.acceptance,
        }


@dataclass(frozen=True)
class ScholarTask:
    task_id: str
    obligation_id: str
    packet_digest: str
    required_expertise: tuple[str, ...]
    reward: dict[str, Any] | None = None  # metadata only; no payment execution
    status: str = "OPEN"

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Adjudication:
    adjudication_id: str
    obligation_id: str
    packet_digest: str
    actor_id: str
    decision: str
    reason: str
    evidence_refs: tuple[str, ...] = ()
    authority: str = "human"

    @property
    def digest(self) -> str:
        return digest_json(self.to_dict())

    def to_dict(self):
        return asdict(self)


def make_packet(question: str, evidence: list[EvidenceItem], expertise: list[str] | None = None, acceptance: dict[str,Any] | None = None) -> EvidencePacket:
    return EvidencePacket("packet:" + uuid.uuid4().hex[:16], question, tuple(evidence), tuple(expertise or []), acceptance or {})


def make_scholar_task(obligation_id: str, packet: EvidencePacket, reward: dict[str,Any] | None = None) -> ScholarTask:
    return ScholarTask("task:" + uuid.uuid4().hex[:16], obligation_id, packet.digest, packet.required_expertise, reward)
