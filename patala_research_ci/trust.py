from __future__ import annotations

"""Risk-sensitive policy gate over provenance lineage."""

from dataclasses import dataclass, asdict
from typing import Iterable

from .lineage import LineageGraph, ArtifactState


@dataclass(frozen=True)
class ActionPolicy:
    action: str
    minimum_path_trust: float = 0.7
    require_current: bool = True
    deny_authorities: tuple[str, ...] = ("untrusted",)
    minimum_human_verified_dependencies: int = 0


@dataclass(frozen=True)
class GateDecision:
    action: str
    target_id: str
    allowed: bool
    reasons: tuple[str, ...]
    minimum_observed_trust: float

    def to_dict(self):
        return asdict(self)


class PolicyEngine:
    def evaluate(self, graph: LineageGraph, target_id: str, policy: ActionPolicy) -> GateDecision:
        if target_id not in graph.nodes:
            return GateDecision(policy.action, target_id, False, ("unknown target",), 0.0)
        target = graph.nodes[target_id]
        reasons: list[str] = []
        if policy.require_current and target.state not in {ArtifactState.CURRENT.value, ArtifactState.VERIFIED_CURRENT.value}:
            reasons.append(f"target state is {target.state}")
        trusts: list[float] = []
        human_verified = 0
        for dep in target.dependencies:
            trusts.append(float(dep.trust))
            if dep.authority == "human_verified":
                human_verified += 1
            if dep.authority in policy.deny_authorities:
                reasons.append(f"dependency {dep.upstream_id} authority={dep.authority}")
        min_trust = min(trusts) if trusts else 1.0
        if min_trust < policy.minimum_path_trust:
            reasons.append(f"trust {min_trust:.3f} below {policy.minimum_path_trust:.3f}")
        if human_verified < policy.minimum_human_verified_dependencies:
            reasons.append("insufficient human-verified dependencies")
        return GateDecision(policy.action, target_id, not reasons, tuple(reasons), min_trust)
