"""Learning mechanisms: Wilson confidence, Thompson Sampling, priority scoring.

Adapted from QDW hotswap/persistent.py and hotswap/stats.py.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional


# --- Wilson Lower Bound ---

def wilson_lower(successes: int, trials: int, z: float = 1.6448536269514722) -> float:
    """One-sided 95% confidence lower bound for success rate.

    From QDW hotswap/stats.py. Guards against overconfident low-sample predictions.
    """
    if trials <= 0:
        return 0.0
    p = successes / trials
    denom = 1.0 + z * z / trials
    centre = p + z * z / (2 * trials)
    adj = z * math.sqrt((p * (1 - p) + z * z / (4 * trials)) / trials)
    return max(0.0, min(1.0, (centre - adj) / denom))


# --- Thompson Sampling Bandit ---

@dataclass
class BetaPosterior:
    """Beta(alpha, beta) posterior for a verification route."""
    alpha: float = 1.0
    beta: float = 1.0

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def trials(self) -> int:
        return int(self.alpha + self.beta - 2)

    def sample(self, rng: random.Random | None = None) -> float:
        r = rng or random.Random()
        return r.betavariate(self.alpha, self.beta)

    def update(self, success: bool, weight: float = 1.0) -> None:
        if success:
            self.alpha += weight
        else:
            self.beta += weight


class ThompsonBandit:
    """Thompson Sampling bandit for verification route selection.

    Adapted from QDW PersistentBanditStore. Each route has a Beta posterior.
    On each verification outcome, alpha increments on success, beta on failure.
    thompson() samples from the posterior for exploration decisions.
    """

    def __init__(self):
        self.posteriors: dict[str, BetaPosterior] = {}

    def get_posterior(self, route_id: str, prior_success: float = 0.5,
                      prior_confidence: float = 0.0) -> BetaPosterior:
        if route_id not in self.posteriors:
            strength = 2.0 + 8.0 * max(0.0, min(1.0, prior_confidence))
            self.posteriors[route_id] = BetaPosterior(
                alpha=1.0 + strength * prior_success,
                beta=1.0 + strength * (1.0 - prior_success),
            )
        return self.posteriors[route_id]

    def update(self, route_id: str, success: bool, weight: float = 1.0) -> None:
        p = self.get_posterior(route_id)
        p.update(success, weight)

    def thompson_sample(self, route_id: str, rng: random.Random | None = None) -> float:
        return self.get_posterior(route_id).sample(rng)

    def best_route(self, candidates: list[str], rng: random.Random | None = None) -> str:
        """Thompson sample each candidate, return the one with highest sample."""
        r = rng or random.Random()
        return max(candidates, key=lambda c: self.thompson_sample(c, r))


# --- Priority Scoring ---

@dataclass
class PriorityScore:
    """Deterministic priority for proof obligations.

    Adapted from QDW next_action.py: P(v) = w1*D + w2*B + w3*U + w4*Q + w5*R - w6*C
    """
    blast_radius: int = 0       # how many downstream objects depend on this
    urgency: float = 0.5        # 0-1, how time-sensitive
    cost: float = 1.0           # estimated recomputation cost
    confidence: float = 0.5     # 0-1, how sure we are this is needed
    recency: float = 0.5        # 0-1, how recently was this verified

    # Weights (from QDW)
    w_blast: float = 0.35
    w_urgency: float = 0.25
    w_confidence: float = 0.20
    w_recency: float = 0.10
    w_cost_inv: float = 0.10    # inverse cost (cheaper = higher priority)

    @property
    def score(self) -> float:
        cost_inv = 1.0 / max(self.cost, 0.01)
        cost_inv_norm = min(1.0, cost_inv)
        return (
            self.w_blast * min(1.0, self.blast_radius / 10.0)
            + self.w_urgency * self.urgency
            + self.w_confidence * self.confidence
            + self.w_recency * self.recency
            + self.w_cost_inv * cost_inv_norm
        )


# --- Blast Radius Calculator ---

def compute_blast_radius(
    dependency_graph: dict[str, set[str]],
    changed: set[str],
) -> dict[str, int]:
    """Compute blast radius for each changed entity.

    Returns {entity_id: count_of_downstream_dependencies}.
    """
    # Build reverse index: who depends on what
    depends_on: dict[str, set[str]] = {k: set() for k in dependency_graph}
    for layer, deps in dependency_graph.items():
        for dep in deps:
            if dep in depends_on:
                depends_on[dep].add(layer)

    # BFS from changed set
    blast = {}
    frontier = set(changed)
    visited = set(changed)
    depth = 1
    while frontier:
        next_frontier = set()
        for node in frontier:
            for downstream in depends_on.get(node, set()):
                if downstream not in visited:
                    visited.add(downstream)
                    blast[downstream] = depth
                    next_frontier.add(downstream)
        frontier = next_frontier
        depth += 1

    return blast
