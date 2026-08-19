from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SourceStatus(str, Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    BLOCKED = "BLOCKED"
    RETIRED = "RETIRED"


class ClaimState(str, Enum):
    CURRENT = "CURRENT"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    RECOMPUTE_REQUIRED = "RECOMPUTE_REQUIRED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"
    VERIFIED_CURRENT = "VERIFIED_CURRENT"
    UNSUPPORTED = "UNSUPPORTED"
    EXPIRED = "EXPIRED"  # absence claim expired — source may have new data


class EpistemicLevel(str, Enum):
    """5-level epistemic ladder from patalapath2 + sanskritbenchy.

    OBSERVED   = directly seen in source
    INFERRED   = derived by algorithm
    ESTIMATED  = computed from partial data
    ASSERTED   = claimed without evidence
    ADJUDICATED = verified by human expert
    """
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    ESTIMATED = "ESTIMATED"
    ASSERTED = "ASSERTED"
    ADJUDICATED = "ADJUDICATED"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Materiality(str, Enum):
    COSMETIC = "COSMETIC"
    IDENTITY = "IDENTITY"
    METADATA = "METADATA"
    RELATION = "RELATION"
    AVAILABILITY = "AVAILABILITY"
    CORRECTION = "CORRECTION"
    RETRACTION = "RETRACTION"
    QUERY_MEMBERSHIP = "QUERY_MEMBERSHIP"
    SOURCE_HEALTH = "SOURCE_HEALTH"


@dataclass(frozen=True)
class QuerySpec:
    entity: str = "research-products"
    search: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    api_version: str = "v3"
    page_size: int = 50
    max_pages: int = 1
    include_scholexplorer: bool = False
    scholexplorer_relation: str | None = None
    select: list[str] = field(default_factory=list)
    facets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "QuerySpec":
        return cls(**d)


@dataclass
class ProviderHealth:
    """Rich source health model from patalapath2."""
    provider_id: str
    last_success: str = ""
    freshness: str = SourceStatus.OK.value
    records_seen: int = 0
    error_rate: float = 0.0
    metadata_yield: float = 1.0
    last_checked: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StalenessRecord:
    """Tracks when an absence claim should expire.

    From patalapath2: "A claim of absence should expire."
    If we searched and found nothing 3 months ago, that absence is stale.
    """
    dimension: str  # e.g. "translation.eng", "dataset.linked"
    state: str  # SEARCHED_FOUND, SEARCHED_NONE_KNOWN, NOT_SEARCHED
    checked_at: str = ""
    search_protocol: str = ""
    freshness: str = "CURRENT"
    expires_at: str | None = None  # when absence claim expires

    def is_expired(self, current_time: str | None = None) -> bool:
        """Check if this staleness record has expired."""
        if self.expires_at is None:
            return False
        if current_time is None:
            return False
        return current_time > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Snapshot:
    snapshot_id: str
    provider: str
    api_version: str
    observed_at: str
    query: dict[str, Any]
    source_status: str
    source_error: str | None
    items: list[dict[str, Any]]
    relations: list[dict[str, Any]]
    header: dict[str, Any]
    digest: str
    raw_digest: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Snapshot":
        return cls(**d)


@dataclass
class Dependency:
    kind: str  # entity | field | relation | query_membership
    entity_id: str | None = None
    field_path: str | None = None
    source: str | None = None
    relation: str | None = None
    target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Dependency":
        return cls(**d)


@dataclass
class TrackedClaim:
    claim_id: str
    text: str
    dependencies: list[Dependency] = field(default_factory=list)
    computation: dict[str, Any] | None = None
    baseline_value: Any = None
    baseline_supported: bool | None = None
    state: str = ClaimState.CURRENT.value
    epistemic_level: str = EpistemicLevel.OBSERVED.value
    confidence: float = 0.0  # Wilson lower bound confidence in state assessment
    blast_radius: int = 0    # downstream objects depending on this claim
    last_verified: str = ""
    absence_expires_at: str | None = None  # from patalapath2: "absence claims should expire"
    is_absence_claim: bool = False  # True if claim is "X does NOT exist"

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["dependencies"] = [d.to_dict() for d in self.dependencies]
        return out

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TrackedClaim":
        x = dict(d)
        x["dependencies"] = [Dependency.from_dict(v) for v in x.get("dependencies", [])]
        return cls(**x)


@dataclass
class TrackedAnalysis:
    analysis_id: str
    title: str
    query: QuerySpec
    created_at: str
    latest_snapshot_id: str
    claims: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["query"] = self.query.to_dict()
        return out

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TrackedAnalysis":
        x = dict(d)
        x["query"] = QuerySpec.from_dict(x["query"])
        return cls(**x)


@dataclass
class Change:
    change_id: str
    kind: str
    materiality: str
    entity_id: str | None = None
    path: str | None = None
    before: Any = None
    after: Any = None
    relation: dict[str, Any] | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Change":
        return cls(**d)


@dataclass
class SemanticDiff:
    diff_id: str
    analysis_id: str
    old_snapshot_id: str
    new_snapshot_id: str
    old_digest: str
    new_digest: str
    source_status: str
    changes: list[Change]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["changes"] = [c.to_dict() for c in self.changes]
        return out

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SemanticDiff":
        x = dict(d)
        x["changes"] = [Change.from_dict(v) for v in x.get("changes", [])]
        return cls(**x)


@dataclass
class ClaimImpact:
    claim_id: str
    state: str
    change_ids: list[str]
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImpactReport:
    impact_id: str
    analysis_id: str
    diff_id: str
    claims: list[ClaimImpact]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "claims": [c.to_dict() for c in self.claims]}


@dataclass
class ProofObligation:
    obligation_id: str
    analysis_id: str
    claim_id: str
    trigger_change_ids: list[str]
    reason: str
    action: str
    status: str = "OPEN"
    resolution_plan_hash: str | None = None
    priority: float = 0.0  # deterministic priority score
    severity: str = Severity.MEDIUM.value
    blast_radius: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResolutionCheck:
    check_id: str
    check_type: str
    params: dict[str, Any] = field(default_factory=dict)
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResolutionPlan:
    plan_id: str
    version: str
    obligation_id: str
    subject_binding: dict[str, Any]
    checks: tuple[ResolutionCheck, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "version": self.version,
            "obligation_id": self.obligation_id,
            "subject_binding": self.subject_binding,
            "checks": [c.to_dict() for c in self.checks],
        }


@dataclass
class VerificationReceipt:
    receipt_id: str
    obligation_id: str
    plan_hash: str
    subject_binding: dict[str, Any]
    checks: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    started_at: str
    finished_at: str
    status: str
    environment: dict[str, Any]
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
