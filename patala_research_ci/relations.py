"""Canonical scholarly relation propositions.

OpenAIRE documents Graph relation pairs such as IsCitedBy/Cites and
IsReferencedBy/References. ScholeXplorer V3 also states that relationships are
stored on the active side of the verb. We therefore compare semantic propositions,
not raw upstream edge spelling.
"""
from __future__ import annotations
from typing import Any

# value = (canonical active label, flip endpoints)
_PAIR = {
    "iscitedby": ("Cites", True), "cites": ("Cites", False),
    "isreferencedby": ("References", True), "references": ("References", False),
    "issupplementedby": ("IsSupplementTo", True), "issupplementto": ("IsSupplementTo", False),
    "ispartof": ("HasPart", True), "haspart": ("HasPart", False),
    "isdocumentedby": ("Documents", True), "documents": ("Documents", False),
    "isobsoletedby": ("Obsoletes", True), "obsoletes": ("Obsoletes", False),
    "isderivedfrom": ("IsSourceOf", True), "issourceof": ("IsSourceOf", False),
    "iscompiledby": ("Compiles", True), "compiles": ("Compiles", False),
    "isrequiredby": ("Requires", True), "requires": ("Requires", False),
    "isreviewedby": ("Reviews", True), "reviews": ("Reviews", False),
    "isvariantformof": ("IsOriginalFormOf", True), "isoriginalformof": ("IsOriginalFormOf", False),
    "isversionof": ("HasVersion", True), "hasversion": ("HasVersion", False),
    "ispreviousversionof": ("IsNewVersionOf", True), "isnewversionof": ("IsNewVersionOf", False),
    "iscontinuedby": ("Continues", True), "continues": ("Continues", False),
    "isparticipant": ("hasParticipant", True), "hasparticipant": ("hasParticipant", False),
    "isproducedby": ("produces", True), "produces": ("produces", False),
    "isrelatedto": ("IsRelatedTo", False),
    "isidenticalto": ("IsIdenticalTo", False),
    "hasamongtopnsimilardocuments": ("HasAmongTopNSimilarDocuments", False),
    "isamongtopnsimilardocuments": ("HasAmongTopNSimilarDocuments", True),
}

def _compact(s: Any) -> str:
    return ''.join(c for c in str(s or '').lower() if c.isalnum())

def canonical_relation(source: Any, relation: Any, target: Any, *, subtype: Any=None) -> dict[str, Any]:
    # ScholeXplorer often returns RelationshipType.Name=IsRelatedTo while the
    # specific semantic is in SubType. Prefer a recognized subtype.
    raw = str(relation or "IsRelatedTo")
    sem = _compact(subtype)
    key = sem if sem in _PAIR else _compact(raw)
    label, flip = _PAIR.get(key, (raw, False))
    s, t = (target, source) if flip else (source, target)
    return {"source": None if s is None else str(s), "relation": label,
            "target": None if t is None else str(t)}

def relation_key(rel: dict[str, Any]) -> tuple[str,str,str]:
    c = canonical_relation(rel.get('source'), rel.get('relation') or rel.get('relationship_name'),
                           rel.get('target'), subtype=rel.get('subtype'))
    return (c['source'] or '', c['relation'], c['target'] or '')

def canonicalize_relation_record(rel: dict[str, Any]) -> dict[str, Any]:
    out = dict(rel)
    c = canonical_relation(rel.get('source'), rel.get('relation') or rel.get('relationship_name'),
                           rel.get('target'), subtype=rel.get('subtype'))
    out.update(c)
    return out
