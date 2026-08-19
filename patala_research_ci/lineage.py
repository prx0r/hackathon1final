from __future__ import annotations

"""Generic provenance/execution lineage kernel.

Inspired by execution-lineage DAGs, provenance-aware agent memory, and build-system
invalidation. It intentionally stores only explicit, auditable dependencies; no
chain-of-thought is required or accepted as provenance.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterable
import uuid

from .canonical import digest_json


class ArtifactState(str, Enum):
    CURRENT = "CURRENT"
    REVERIFY_REQUIRED = "REVERIFY_REQUIRED"
    BLOCKED = "BLOCKED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    VERIFIED_CURRENT = "VERIFIED_CURRENT"
    UNSUPPORTED = "UNSUPPORTED"


class ArtifactKind(str, Enum):
    OBSERVATION = "observation"
    CLAIM = "claim"
    CALCULATION = "calculation"
    SECTION = "section"
    REPORT = "report"
    RECOMMENDATION = "recommendation"
    MEMORY = "memory"
    REVIEW_FINDING = "review_finding"
    ADJUDICATION = "adjudication"


@dataclass(frozen=True)
class LineageEdge:
    upstream_id: str
    kind: str = "depends_on"
    trust: float = 1.0
    required: bool = True
    authority: str = "observed"  # observed | machine_proposed | human_verified
    selector: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not 0.0 <= float(self.trust) <= 1.0:
            raise ValueError("trust must be in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LineageArtifact:
    logical_id: str
    kind: str
    content: Any
    specification: dict[str, Any] = field(default_factory=dict)
    dependencies: list[LineageEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    state: str = ArtifactState.CURRENT.value
    artifact_id: str = ""
    content_digest: str = ""
    execution_key: str = ""

    def finalize(self, upstream_execution_keys: dict[str, str] | None = None) -> "LineageArtifact":
        upstream_execution_keys = upstream_execution_keys or {}
        self.content_digest = digest_json(self.content)
        identity_body = {
            "logical_id": self.logical_id,
            "kind": self.kind,
            "specification": self.specification,
            # Source/observation nodes have no upstream execution identity, so their
            # observed content is the resolved input surface. Derived nodes inherit
            # content sensitivity through upstream execution keys.
            "input_content_digest": self.content_digest if not self.dependencies else None,
            "dependencies": [
                {
                    **d.to_dict(),
                    "upstream_execution_key": upstream_execution_keys.get(d.upstream_id, d.upstream_id),
                }
                for d in sorted(self.dependencies, key=lambda x: (x.upstream_id, x.kind))
            ],
        }
        self.execution_key = digest_json(identity_body)
        self.artifact_id = f"artifact:{self.content_digest.split(':')[-1][:20]}"
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "logical_id": self.logical_id,
            "kind": self.kind,
            "content": self.content,
            "specification": self.specification,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "metadata": self.metadata,
            "state": self.state,
            "artifact_id": self.artifact_id,
            "content_digest": self.content_digest,
            "execution_key": self.execution_key,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LineageArtifact":
        x = dict(d)
        x["dependencies"] = [LineageEdge(**e) for e in x.get("dependencies", [])]
        return cls(**x)


class LineageGraph:
    """Small in-memory DAG used for deterministic invalidation and replay planning."""

    def __init__(self):
        self.nodes: dict[str, LineageArtifact] = {}
        self.downstream: dict[str, set[str]] = {}

    def add(self, artifact: LineageArtifact) -> LineageArtifact:
        if artifact.logical_id in self.nodes:
            raise ValueError(f"duplicate logical_id: {artifact.logical_id}")
        for dep in artifact.dependencies:
            if dep.upstream_id not in self.nodes:
                raise KeyError(f"unknown upstream dependency: {dep.upstream_id}")
        upstream_keys = {k: v.execution_key for k, v in self.nodes.items()}
        artifact.finalize(upstream_keys)
        self.nodes[artifact.logical_id] = artifact
        self.downstream.setdefault(artifact.logical_id, set())
        for dep in artifact.dependencies:
            self.downstream.setdefault(dep.upstream_id, set()).add(artifact.logical_id)
        self._assert_dag()
        return artifact

    def _assert_dag(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(n: str):
            if n in visiting:
                raise ValueError("lineage cycle detected")
            if n in visited:
                return
            visiting.add(n)
            for child in self.downstream.get(n, ()):
                visit(child)
            visiting.remove(n)
            visited.add(n)
        for n in self.nodes:
            visit(n)

    def descendants(self, roots: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        stack = list(roots)
        while stack:
            n = stack.pop()
            for child in self.downstream.get(n, ()):
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
        return sorted(seen)

    def invalidation_plan(self, changed_ids: Iterable[str]) -> dict[str, Any]:
        changed = sorted(set(changed_ids))
        missing = [x for x in changed if x not in self.nodes]
        if missing:
            raise KeyError(f"unknown changed nodes: {missing}")
        affected = self.descendants(changed)
        unaffected = sorted(set(self.nodes) - set(changed) - set(affected))
        return {
            "changed": changed,
            "affected": affected,
            "unaffected": unaffected,
            "recompute_count": len(affected),
            "recompute_avoided": len(unaffected),
        }

    def mark_invalidated(self, changed_ids: Iterable[str]) -> dict[str, Any]:
        plan = self.invalidation_plan(changed_ids)
        for node_id in plan["affected"]:
            node = self.nodes[node_id]
            node.state = ArtifactState.REVERIFY_REQUIRED.value
        return plan

    def max_path_trust(self, source_id: str, target_id: str) -> float:
        """Maximum multiplicative trust path, following the MAP-Graph intuition."""
        if source_id == target_id:
            return 1.0
        best: dict[str, float] = {source_id: 1.0}
        frontier = [source_id]
        while frontier:
            cur = frontier.pop()
            cur_score = best[cur]
            for child in self.downstream.get(cur, ()):
                edge = next(e for e in self.nodes[child].dependencies if e.upstream_id == cur)
                score = cur_score * edge.trust
                if score > best.get(child, -1.0):
                    best[child] = score
                    frontier.append(child)
        return max(0.0, best.get(target_id, 0.0))

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": [self.nodes[k].to_dict() for k in sorted(self.nodes)]}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LineageGraph":
        g = cls()
        pending = [LineageArtifact.from_dict(x) for x in d.get("nodes", [])]
        # Topologically add from dependencies. Fail if no progress.
        while pending:
            progress = False
            for art in list(pending):
                if all(e.upstream_id in g.nodes for e in art.dependencies):
                    # Preserve serialized identity by re-finalizing; deterministic equality is testable.
                    g.add(LineageArtifact(
                        logical_id=art.logical_id, kind=art.kind, content=art.content,
                        specification=art.specification, dependencies=art.dependencies,
                        metadata=art.metadata, state=art.state,
                    ))
                    pending.remove(art)
                    progress = True
            if not progress:
                raise ValueError("cannot restore lineage graph; missing deps or cycle")
        return g


def new_logical_id(kind: str) -> str:
    return f"{kind}:{uuid.uuid4().hex[:16]}"
