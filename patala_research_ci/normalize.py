from __future__ import annotations

from typing import Any

from .canonical import digest_json


def _first(d: dict[str, Any], *keys: str, default=None):
    for key in keys:
        if key in d and d[key] not in (None, "", []):
            return d[key]
    return default


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for k in ("label", "value", "$", "name", "fullName", "fullname"):
            if value.get(k):
                return str(value[k]).strip()
    return str(value).strip()


def _normalise_pids(raw: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if isinstance(raw, dict):
        # V4 may expose an ids/pids mapping, e.g. {"doi": [..]}
        for scheme, vals in raw.items():
            if not isinstance(vals, list):
                vals = [vals]
            for v in vals:
                val = _text(v)
                if val:
                    out.append({"scheme": str(scheme).lower(), "value": val.lower() if str(scheme).lower() == "doi" else val})
    elif isinstance(raw, list):
        for v in raw:
            if isinstance(v, dict):
                scheme = str(_first(v, "scheme", "type", "classid", "@classid", default="pid")).lower()
                val = _text(_first(v, "value", "id", "$", "identifier"))
                if val:
                    out.append({"scheme": scheme, "value": val.lower() if scheme == "doi" else val})
            else:
                val = _text(v)
                if val:
                    out.append({"scheme": "pid", "value": val})
    elif raw:
        out.append({"scheme": "pid", "value": _text(raw) or ""})
    unique = {(x["scheme"], x["value"]): x for x in out if x.get("value")}
    return [unique[k] for k in sorted(unique)]


def _normalise_authors(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []
    if isinstance(raw, dict):
        raw = [raw]
    out = []
    for a in raw if isinstance(raw, list) else []:
        if not isinstance(a, dict):
            out.append({"name": _text(a)})
            continue
        author = a.get("author") if isinstance(a.get("author"), dict) else a
        name = _text(_first(author, "fullName", "fullname", "name"))
        # Graph V3/V4 author PID shape is commonly:
        # {"pid": {"id": {"scheme": "orcid", "value": "0000-..."}, ...}}.
        # Keep compatibility with flatter ORCID/id variants as well.
        orcid = _text(_first(author, "orcid"))
        if not orcid:
            flat_id = _text(_first(author, "id"))
            if flat_id and flat_id.startswith("0000-"):
                orcid = flat_id
        if not orcid and isinstance(author.get("pid"), dict):
            pid_id = author["pid"].get("id")
            if isinstance(pid_id, dict) and str(pid_id.get("scheme", "")).lower() == "orcid":
                orcid = _text(pid_id.get("value"))
        institutions = a.get("institutions") or a.get("affiliations") or []
        if isinstance(institutions, dict):
            institutions = [institutions]
        insts = []
        for inst in institutions if isinstance(institutions, list) else []:
            if isinstance(inst, dict):
                insts.append({
                    "id": _text(_first(inst, "id", "organizationId", "ror")),
                    "name": _text(_first(inst, "name", "legalName", "label")),
                    "country": _text(_first(inst, "country", "countryCode")),
                })
        out.append({"name": name, "orcid": orcid, "institutions": insts})
    return out


def _normalise_grants(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []
    if isinstance(raw, dict):
        raw = [raw]
    out = []
    for g in raw if isinstance(raw, list) else []:
        if not isinstance(g, dict):
            continue
        out.append({
            "project_id": _text(_first(g, "projectId", "project_id", "id")),
            "code": _text(_first(g, "code", "grantCode")),
            "funder": _text(_first(g, "funderShortName", "funder_short_name", "funder")),
            "funding_stream": _text(_first(g, "fundingStreamId", "funding_stream_id")),
        })
    out.sort(key=lambda x: (x.get("project_id") or "", x.get("code") or ""))
    return out


def normalize_entity(raw: dict[str, Any], entity_type: str = "research-products") -> dict[str, Any]:
    """Normalize V3/V4 records into a deliberately small, stable semantic record.

    We retain the raw canonical digest so unknown/new OpenAIRE fields are still detectable
    without coupling the impact engine to every API schema detail.
    """
    rid = _text(_first(raw, "id", "openAireId", "openaireId", "identifier")) or digest_json(raw)[:32]
    typ = _text(_first(raw, "type", "entityType", default=entity_type.rstrip("s")))
    title = _text(_first(raw, "mainTitle", "maintitle", "title", "legalName", "officialName", "acronym", "fullName"))
    publication_date = _text(_first(raw, "publicationDate", "dateOfAcceptance", "dateofacceptance", "startDate"))
    access = _first(raw, "bestAccessRight", "bestaccessright", "best_oa", "accessRight", "access_right")
    if isinstance(access, dict):
        access = _text(_first(access, "label", "rights", "name", "$", "@classid"))
    else:
        access = _text(access)
    pids = _normalise_pids(_first(raw, "pids", "ids", "pid", "identifiers", default=[]))
    authors = _normalise_authors(_first(raw, "authors", "author", "authorships", "creator", default=[]))
    grants = _normalise_grants(_first(raw, "grants", "projects", "funding", default=[]))
    publisher = _text(_first(raw, "publisher", "hostedBy", "journal"))
    language = _text(_first(raw, "language", "languages"))
    peer = _first(raw, "isPeerReviewed", "is_peer_reviewed", "peerReviewed")
    corrected = bool(_first(raw, "isCorrected", "corrected", default=False))
    retracted = bool(_first(raw, "isRetracted", "retracted", default=False))
    return {
        "id": rid,
        "entity_type": entity_type,
        "type": typ,
        "title": title,
        "publication_date": publication_date,
        "access_right": access,
        "publisher": publisher,
        "language": language,
        "is_peer_reviewed": peer,
        "is_corrected": corrected,
        "is_retracted": retracted,
        "pids": pids,
        "authors": authors,
        "grants": grants,
        "raw_digest": digest_json(raw, drop_volatile=True),
    }


def primary_pid(entity: dict[str, Any]) -> str | None:
    pids = entity.get("pids") or []
    priority = {"doi": 0, "pmid": 1, "arxiv": 2, "handle": 3, "pid": 9}
    ranked = sorted(pids, key=lambda x: (priority.get(str(x.get("scheme")).lower(), 5), x.get("value") or ""))
    return ranked[0]["value"] if ranked else None


_SCHOLIX_SEMANTICS = {
    "cites": "Cites",
    "issourceof": "IsSourceOf",
    "isrelatedto": "IsRelatedTo",
    "references": "References",
    "haspart": "HasPart",
    "issupplementto": "IsSupplementTo",
    "isnewversionof": "IsNewVersionOf",
    "hasversion": "HasVersion",
    "continues": "Continues",
    "documents": "Documents",
    "isidenticalto": "IsIdenticalTo",
    "isoriginalformof": "IsOriginalFormOf",
    "reviews": "Reviews",
    "compiles": "Compiles",
    "obsoletes": "Obsoletes",
    "describes": "Describes",
    "requires": "Requires",
    "ismetadataof": "IsMetadataOf",
}


def _canonical_scholix_semantic(name: str, subtype: str | None) -> str:
    # ScholeXplorer responses sometimes retain the generic Name=IsRelatedTo while
    # encoding the requested active semantic (e.g. cites) in SubType. Prefer the
    # specific known semantic while retaining both fields in the normalized record.
    compact = "".join(c for c in (subtype or "").lower() if c.isalnum())
    if compact in _SCHOLIX_SEMANTICS:
        return _SCHOLIX_SEMANTICS[compact]
    name_compact = "".join(c for c in name.lower() if c.isalnum())
    return _SCHOLIX_SEMANTICS.get(name_compact, name)


def normalize_scholexplorer_link(raw: dict[str, Any]) -> dict[str, Any]:
    rt = raw.get("RelationshipType") or raw.get("relationshipType") or {}
    name = _text(_first(rt, "Name", "name", default="IsRelatedTo")) or "IsRelatedTo"
    subtype = _text(_first(rt, "SubType", "subType"))
    semantic = _canonical_scholix_semantic(name, subtype)

    def endpoint(name_: str) -> dict[str, Any]:
        x = raw.get(name_) or {}
        ids = x.get("Identifier") or x.get("identifier") or []
        if isinstance(ids, dict):
            ids = [ids]
        pid = None
        for ident in ids if isinstance(ids, list) else []:
            if isinstance(ident, dict):
                pid = _text(_first(ident, "ID", "id", "value"))
                if pid:
                    break
        return {
            "pid": pid,
            "type": _text(_first(x, "Type", "type")),
            "publisher": _text(_first(x, "Publisher", "publisher")),
        }

    source = endpoint("source")
    target = endpoint("target")
    return {
        "source": source.get("pid"),
        "target": target.get("pid"),
        "relation": semantic,
        "relationship_name": name,
        "subtype": subtype,
        "source_type": source.get("type"),
        "target_type": target.get("type"),
        "source_publisher": source.get("publisher"),
        "target_publisher": target.get("publisher"),
        "raw_digest": digest_json(raw, drop_volatile=True),
    }
