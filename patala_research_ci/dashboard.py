from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .store import Workspace


HTML = r'''<!doctype html>
<html><head><meta charset="utf-8"><title>Pāṭala Research CI</title>
<style>
body{font-family:system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 20px;color:#171717}
h1{font-size:2.2rem;margin-bottom:.2rem}.sub{color:#555;margin-bottom:2rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.card{border:1px solid #ddd;border-radius:12px;padding:16px;background:#fff}.k{font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;color:#666}
.badge{display:inline-block;padding:3px 8px;border:1px solid #bbb;border-radius:999px;font-size:.8rem;margin-right:6px}
pre{white-space:pre-wrap;background:#f6f6f6;padding:12px;border-radius:8px;overflow:auto}
</style></head><body>
<h1>Pāṭala Research CI</h1><div class="sub">When the evidence changes, know what to recheck.</div>
<div id="summary" class="grid"></div><h2>Open proof obligations</h2><div id="obs"></div>
<script>
async function load(){const s=await (await fetch('/api/status')).json();
 document.getElementById('summary').innerHTML=`<div class=card><div class=k>Analyses</div><h2>${s.analyses.length}</h2></div><div class=card><div class=k>Open obligations</div><h2>${s.obligations.filter(x=>x.status==='OPEN').length}</h2></div><div class=card><div class=k>Ledger</div><h2>${s.ledger_ok?'VERIFIED':'BROKEN'}</h2><code>${s.state_digest.slice(0,28)}…</code></div>`;
 const o=s.obligations;document.getElementById('obs').innerHTML=o.length?o.map(x=>`<div class=card style="margin-bottom:10px"><span class=badge>${x.status}</span><span class=badge>${x.action}</span><h3>${x.claim_id}</h3><p>${x.reason}</p><code>${x.obligation_id}</code></div>`).join(''):'<p>No obligations.</p>';}
load();</script></body></html>'''


def serve(workspace: str | Path = ".patala-ci", host: str = "127.0.0.1", port: int = 8765):
    ws = Workspace(workspace)

    class Handler(BaseHTTPRequestHandler):
        def _json(self, data, status=200):
            raw = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                raw = HTML.encode("utf-8"); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw); return
            if path == "/api/status":
                ok, reason = ws.ledger.verify()
                self._json({"analyses": ws.list_analyses(), "obligations": ws.list_obligations(),
                            "ledger_ok": ok, "ledger_reason": reason, "state_digest": ws.ledger.state_digest()}); return
            self._json({"error":"not found"}, 404)

        def log_message(self, fmt, *args):
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Pāṭala Research CI dashboard: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
