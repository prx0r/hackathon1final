from __future__ import annotations

import json
import zipfile
from pathlib import Path

from .canonical import digest_json
from .store import Workspace


def export_ro_crate(ws: Workspace, analysis_id: str, out_path: str | Path) -> Path:
    """Export an interoperable research object bundle using the RO-Crate file layout.

    This is a lightweight writer, intentionally avoiding a hard dependency on ro-crate-py.
    """
    out_path = Path(out_path)
    analysis = ws.load_analysis(analysis_id)
    related = []
    files: list[Path] = []
    for folder in ("analyses", "snapshots", "claims", "diffs", "impacts", "obligations", "plans", "receipts", "mcp_traces"):
        for p in sorted((ws.root / folder).glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            blob = json.dumps(data, sort_keys=True)
            if analysis_id in blob or p.name == _safe(analysis_id) + ".json":
                files.append(p)
    graph = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "about": {"@id": "./"},
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
        },
        {
            "@id": "./",
            "@type": "Dataset",
            "name": f"Pāṭala Research CI export: {analysis.title}",
            "description": analysis.description or "Tracked OpenAIRE analysis with snapshots, claims, impacts and proof receipts.",
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "hasPart": [{"@id": f"data/{p.parent.name}/{p.name}"} for p in files],
        },
    ]
    for p in files:
        rel = f"data/{p.parent.name}/{p.name}"
        graph.append({"@id": rel, "@type": "File", "name": p.name})
    metadata = {"@context": "https://w3id.org/ro/crate/1.2/context", "@graph": graph}
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("ro-crate-metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))
        zf.writestr("manifest.json", json.dumps({
            "analysis_id": analysis_id,
            "analysis_digest": digest_json(analysis.to_dict()),
            "file_count": len(files),
        }, indent=2))
        for p in files:
            zf.write(p, f"data/{p.parent.name}/{p.name}")
        if ws.ledger.path.exists():
            zf.write(ws.ledger.path, "data/ledger.jsonl")
    return out_path


def _safe(key: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in key)
