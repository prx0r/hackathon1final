from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from .model import SourceStatus


@dataclass
class JsonResponse:
    status: str
    body: dict[str, Any] | None
    url: str
    http_status: int | None = None
    error: str | None = None


class JsonTransport:
    """Small injectable HTTP transport with typed source failure semantics."""

    def __init__(self, timeout: float = 30.0, retries: int = 3, user_agent: str = "patala-research-ci/0.1"):
        self.timeout = timeout
        self.retries = retries
        self.user_agent = user_agent

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> JsonResponse:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        full = url
        if params:
            full += ("&" if "?" in full else "?") + urllib.parse.urlencode(params, doseq=True)
        req = urllib.request.Request(full, headers={"Accept": "application/json", "User-Agent": self.user_agent})
        last_error: str | None = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    return JsonResponse(SourceStatus.OK.value, json.loads(raw.decode("utf-8")), full, int(resp.status), None)
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP {exc.code}: {exc.reason}"
                if exc.code not in {429, 500, 502, 503, 504}:
                    break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = str(exc)
            if attempt + 1 < self.retries:
                time.sleep(0.2 * (2 ** attempt))
        return JsonResponse(SourceStatus.UNAVAILABLE.value, None, full, None, last_error or "request failed")


class FunctionTransport:
    """Test transport. Handler receives (url, params) and returns dict or raises."""

    def __init__(self, handler: Callable[[str, dict[str, Any]], dict[str, Any]]):
        self.handler = handler

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> JsonResponse:
        try:
            body = self.handler(url, params or {})
            return JsonResponse(SourceStatus.OK.value, body, url, 200, None)
        except Exception as exc:  # intentionally converts test/live adapter exceptions to typed failure
            return JsonResponse(SourceStatus.UNAVAILABLE.value, None, url, None, str(exc))
