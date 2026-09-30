"""Web UI (stdlib only): submit a report, act as the human reviewer, inspect the trace, view the observability dashboard.

Security posture (this is a public-facing demo of a governed system):
- reports are processed in memory; raw text is never written to disk (same as the CLI)
- nothing is released until a person clicks Approve; reviews time out to "pending"
- optional REVIEWER_TOKEN env var must be supplied to approve/reject
- bounded body size, bounded concurrent runs, strict CSP, all output HTML-escaped
"""
import hmac
import html
import json
import os
import re
import shutil
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .config import ROOT
from .hitl import ExternalHITL
from .mcp_client import MCPClient
from .observability import aggregate
from .state import Memory
from .supervisor import Supervisor

MAX_BODY, MAX_RUNS, MAX_ACTIVE = 20_000, 200, 8
RUN_ID = re.compile(r"^web-[0-9a-f]{12}$")
FILES = {"report.md", "traceability.md", "traceability.json", "trace.jsonl", "metrics.json", "state.json"}
CSS = """body{font:15px system-ui,sans-serif;max-width:1000px;margin:24px auto;padding:0 16px;color:#1b1f24}
nav a{margin-right:14px}pre{background:#f5f6f8;padding:12px;overflow:auto;border-radius:6px;white-space:pre-wrap}
table{border-collapse:collapse;width:100%;font-size:13px}td,th{border:1px solid #d0d7de;padding:4px 8px;text-align:left}
th{background:#f0f2f5}textarea{width:100%;height:280px;font:13px monospace}.badge{padding:2px 10px;border-radius:12px;color:#fff}
.COMPLETED{background:#1a7f37}.PENDING_APPROVAL,.AWAITING_APPROVAL{background:#bf8700}.REJECTED_BY_HUMAN,.ERROR{background:#cf222e}.RUNNING{background:#0969da}
.warn{background:#fff8c5;border:1px solid #d4a72c;padding:8px 12px;border-radius:6px}button{padding:6px 16px;margin-right:8px}"""


def esc(x):
    return html.escape(str(x))


def page(title, body, refresh=False):
    meta = '<meta http-equiv="refresh" content="2">' if refresh else ""
    return (f"<!doctype html><meta charset=utf-8>{meta}<title>{esc(title)}</title><style>{CSS}</style>"
            f'<nav><a href="/">New case</a><a href="/dashboard">Dashboard</a><a href="/healthz">Health</a></nav>'
            f"<h1>{esc(title)}</h1>{body}"
            "<p><small>Training prototype · synthetic data · proposals only, not regulatory determinations.</small></p>").encode()


class App:
    def __init__(self, out_dir=None):
        self.out = Path(out_dir or os.environ.get("PV_OUT_DIR", ROOT / "output" / "web"))
        self.runs_dir = self.out / "runs"
        self.memory = Memory(self.out / "memory.json")
        self.timeout = int(os.environ.get("APPROVAL_TIMEOUT", "900"))
        self.token = os.environ.get("REVIEWER_TOKEN")
        self.runs, self.lock = {}, threading.Lock()

    def start(self, text):
        with self.lock:
            if sum(not r["done"].is_set() for r in self.runs.values()) >= MAX_ACTIVE:
                return None
            run_id = "web-" + uuid.uuid4().hex[:12]
            entry = {"id": run_id, "hitl": ExternalHITL(self.timeout), "done": threading.Event(),
                     "status": None, "error": None, "created": time.time()}
            self.runs[run_id] = entry
            for old in sorted((r for r in self.runs.values() if r["done"].is_set()), key=lambda r: r["created"]):
                if len(self.runs) <= MAX_RUNS:
                    break
                self.runs.pop(old["id"])
                shutil.rmtree(self.runs_dir / old["id"], ignore_errors=True)
        threading.Thread(target=self._work, args=(entry, text), daemon=True).start()
        return run_id

    def _work(self, entry, text):
        try:
            with MCPClient() as mcp:
                entry["status"] = Supervisor(mcp, self.memory, entry["hitl"], self.out).process_text(
                    text, entry["id"], "web").status
        except Exception as exc:  # surfaced in the UI, never silently dropped
            entry["status"], entry["error"] = "ERROR", repr(exc)
        finally:
            entry["done"].set()

    def status(self, run_id):
        e = self.runs.get(run_id)
        if e:
            return e["status"] if e["done"].is_set() else ("AWAITING_APPROVAL" if e["hitl"].waiting else "RUNNING")
        f = self.runs_dir / run_id / "state.json"
        return json.loads(f.read_text())["status"] if f.exists() else None

    def read(self, run_id, name):
        f = self.runs_dir / run_id / name
        return f.read_text(encoding="utf-8") if name in FILES and f.exists() else None


def samples():
    return sorted(p.stem for p in (ROOT / "data" / "cases").glob("case_*.txt"))


def home(app, query):
    sample = query.get("sample", [""])[0]
    text = ""
    if re.fullmatch(r"case_\d{3}", sample) and (ROOT / "data" / "cases" / f"{sample}.txt").exists():
        text = (ROOT / "data" / "cases" / f"{sample}.txt").read_text(encoding="utf-8")
    links = " · ".join(f'<a href="/?sample={s}">{s}</a>' for s in samples())
    recent = "".join(f'<li><a href="/run/{r["id"]}">{r["id"]}</a> <span class="badge {app.status(r["id"])}">{app.status(r["id"])}</span></li>'
                     for r in sorted(app.runs.values(), key=lambda r: -r["created"])[:8])
    return page("PV-Triage: adverse-event case triage", f"""
<p>Paste an adverse-event report (labelled-line format) or load a synthetic sample: {links}</p>
<form method=post action=/run><textarea name=report maxlength={MAX_BODY} required>{esc(text)}</textarea>
<p><button>Run agents</button> Any route except <code>routine</code> waits for <b>your</b> approval before release.</p></form>
<h3>Recent runs</h3><ul>{recent or '<li>none yet</li>'}</ul>""")


def run_page(app, run_id):
    status = app.status(run_id)
    if status is None:
        return None
    e = app.runs.get(run_id)
    body = [f'<p><span class="badge {status}">{esc(status)}</span> run <code>{esc(run_id)}</code></p>']
    if e and e["error"]:
        body.append(f'<p class=warn>Run failed: {esc(e["error"])}</p>')
    if status == "AWAITING_APPROVAL":
        tok = '<p><label>Reviewer token <input type=password name=token></label></p>' if app.token else ""
        body.append(f"""<h2>Human review required</h2><pre>{esc(e["hitl"].summary)}</pre>
<form method=post action=/run/{run_id}/decision>{tok}<p><label>Reviewer <input name=reviewer maxlength=60 required></label>
<label>Comment <input name=comment maxlength=300 size=40></label></p>
<button name=decision value=approved>Approve</button><button name=decision value=rejected>Reject</button></form>
<p><small>No response within {app.timeout}s leaves the case pending and nothing is released.</small></p>""")
    elif status == "RUNNING":
        body.append("<p>Agents working…</p>")
    else:
        report = app.read(run_id, "report.md") or ""
        trace = app.read(run_id, "traceability.md") or ""
        rows = ""
        for line in (app.read(run_id, "trace.jsonl") or "").splitlines():
            s = json.loads(line)
            rows += (f"<tr><td>{esc(s['id'])}</td><td>{esc(s['kind'])}</td><td>{esc(s['agent'])}</td><td>{esc(s['name'])}</td>"
                     f"<td>{esc(s['status'])}</td><td>{s['latency_ms']}</td><td>{s['tokens_in']}/{s['tokens_out']}</td></tr>")
        links = " · ".join(f'<a href="/run/{run_id}/{f}">{f}</a>' for f in sorted(FILES))
        body.append(f"<h2>Case report</h2><pre>{esc(report)}</pre><h2>Traceability</h2><pre>{esc(trace)}</pre>"
                    f"<details><summary>All spans (observability)</summary><table><tr><th>id<th>kind<th>agent<th>name<th>status<th>ms<th>tok in/out</tr>{rows}</table></details>"
                    f"<p>Raw: {links}</p>")
    return page(f"Run {run_id}", "".join(body), refresh=status == "RUNNING")


def dashboard(app):
    a = aggregate(app.runs_dir)
    t = a["totals"]
    kv = lambda d: "".join(f"<tr><td>{esc(k)}<td>{esc(v)}</tr>" for k, v in sorted(d.items())) or "<tr><td colspan=2>none</tr>"
    lat = "".join(f"<tr><td>{r['kind']}<td>{esc(r['name'])}<td>{r['calls']}<td>{r['avg_ms']}<td>{r['p95_ms']}<td>{r['max_ms']}<td>{r['errors']}</tr>"
                  for r in a["latency"]) or "<tr><td colspan=7>no finished runs yet</tr>"
    return page("Observability dashboard", f"""
<p>{t['runs']} finished runs · {t['spans']} spans · {t['errors']} errors · {t['guardrail_blocks']} guardrail blocks ·
est. tokens in/out {t['tokens_in_est']}/{t['tokens_out_est']} (deterministic engine: estimates)</p>
<table><tr><th colspan=2>Outcome</tr>{kv(a['status'])}</table><br>
<table><tr><th colspan=2>Route</tr>{kv(a['routes'])}</table><br>
<table><tr><th colspan=2>MCP tool calls</tr>{kv(a['tool_calls'])}</table><br>
<table><tr><th>kind<th>name<th>calls<th>avg ms<th>p95 ms<th>max ms<th>errors</tr>{lat}</table>
<p><a href="/api/metrics">JSON</a></p>""")


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PVTriage/1.0"

        def _send(self, code, body, ctype="text/html; charset=utf-8", extra=None):
            if isinstance(body, str):
                body = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _redirect(self, where):
            self._send(303, b"", extra={"Location": where})

        def _form(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY + 2000:
                return None
            return parse_qs(self.rfile.read(n).decode("utf-8", "replace"))

        def do_GET(self):
            u = urlparse(self.path)
            parts = [p for p in u.path.split("/") if p]
            if u.path == "/":
                return self._send(200, home(app, parse_qs(u.query)))
            if u.path == "/healthz":
                return self._send(200, "ok", "text/plain")
            if u.path == "/dashboard":
                return self._send(200, dashboard(app))
            if u.path == "/api/metrics":
                return self._send(200, json.dumps(aggregate(app.runs_dir)), "application/json")
            if len(parts) >= 2 and parts[0] == "run" and RUN_ID.match(parts[1]):
                if len(parts) == 2:
                    body = run_page(app, parts[1])
                    return self._send(200, body) if body else self._send(404, "not found", "text/plain")
                if len(parts) == 3:
                    text = app.read(parts[1], parts[2])
                    if text is not None:
                        return self._send(200, text, "text/plain; charset=utf-8")
            self._send(404, "not found", "text/plain")

        def do_POST(self):
            parts = [p for p in urlparse(self.path).path.split("/") if p]
            form = self._form()
            if form is None:
                return self._send(413, "request too large", "text/plain")
            if parts == ["run"]:
                text = form.get("report", [""])[0].strip()
                if not text or len(text) > MAX_BODY:
                    return self._send(400, "report missing or too long", "text/plain")
                run_id = app.start(text)
                return self._redirect(f"/run/{run_id}") if run_id else self._send(429, "busy, retry shortly", "text/plain")
            if len(parts) == 3 and parts[0] == "run" and parts[2] == "decision" and RUN_ID.match(parts[1]):
                entry = app.runs.get(parts[1])
                if not entry:
                    return self._send(404, "not found", "text/plain")
                if app.token and not hmac.compare_digest(form.get("token", [""])[0], app.token):
                    return self._send(403, "reviewer token invalid", "text/plain")
                entry["hitl"].submit(form.get("decision", [""])[0], form.get("reviewer", [""])[0], form.get("comment", [""])[0])
                return self._redirect(f"/run/{parts[1]}")
            self._send(404, "not found", "text/plain")

    return Handler


def serve(host=None, port=None, out_dir=None):
    app = App(out_dir)
    host, port = host or os.environ.get("HOST", "127.0.0.1"), int(port or os.environ.get("PORT", "8000"))
    srv = ThreadingHTTPServer((host, port), make_handler(app))
    print(f"PV-Triage web UI on http://{host}:{srv.server_address[1]}", flush=True)
    return srv


if __name__ == "__main__":
    serve().serve_forever()
