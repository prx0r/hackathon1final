from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canonical import digest_json


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class Ledger:
    """Portable append-only hash-chained JSONL event ledger."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def _events(self) -> list[dict[str, Any]]:
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out

    def append(self, event_type: str, subject: str, payload: dict[str, Any]) -> dict[str, Any]:
        events = self._events()
        prev = events[-1]["event_hash"] if events else "GENESIS"
        body = {
            "seq": len(events) + 1,
            "event_type": event_type,
            "subject": subject,
            "observed_at": utc_now(),
            "prev_hash": prev,
            "payload": payload,
        }
        body["event_hash"] = digest_json(body)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        return body

    def verify(self) -> tuple[bool, str]:
        prev = "GENESIS"
        for idx, event in enumerate(self._events(), start=1):
            if event.get("seq") != idx:
                return False, f"sequence mismatch at {idx}"
            if event.get("prev_hash") != prev:
                return False, f"previous hash mismatch at {idx}"
            stored = event.get("event_hash")
            body = {k: v for k, v in event.items() if k != "event_hash"}
            if digest_json(body) != stored:
                return False, f"event hash mismatch at {idx}"
            prev = stored
        return True, "ok"

    def state_digest(self) -> str:
        events = self._events()
        return events[-1]["event_hash"] if events else "GENESIS"

    def events(self) -> list[dict[str, Any]]:
        return self._events()
