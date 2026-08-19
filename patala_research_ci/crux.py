from __future__ import annotations

"""Structural crux analysis over explicit dependency graphs.

A crux here is not 'important text'; it is an upstream node whose invalidation has
large or conclusion-reaching downstream effect.
"""

from dataclasses import dataclass, asdict
from .lineage import LineageGraph


@dataclass(frozen=True)
class CruxScore:
    node_id: str
    descendants: int
    target_hits: int
    score: float

    def to_dict(self):
        return asdict(self)


def rank_cruxes(graph: LineageGraph, target_ids: list[str]) -> list[CruxScore]:
    targets = set(target_ids)
    out = []
    for node_id in graph.nodes:
        descendants = set(graph.descendants([node_id]))
        hits = len(descendants & targets)
        if hits:
            score = hits / max(1, len(targets)) + len(descendants) / max(1, len(graph.nodes))
            out.append(CruxScore(node_id, len(descendants), hits, score))
    return sorted(out, key=lambda x: (-x.score, x.node_id))
