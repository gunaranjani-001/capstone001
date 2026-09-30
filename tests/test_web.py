import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

from pvagent.config import ROOT
from pvagent.web import App, make_handler
from http.server import ThreadingHTTPServer


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


class TestWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.app = App(cls.tmp.name)
        cls.app.timeout = 2
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.app))
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.opener = urllib.request.build_opener(NoRedirect)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.tmp.cleanup()

    def post(self, path, **form):
        data = urllib.parse.urlencode(form).encode()
        try:
            r = self.opener.open(urllib.request.Request(self.base + path, data=data))
            return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read()

    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path) as r:
                return r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    def submit(self, case):
        text = (ROOT / "data" / "cases" / f"{case}.txt").read_text()
        code, headers, _ = self.post("/run", report=text)
        self.assertEqual(code, 303)
        return headers["Location"].rsplit("/", 1)[1]

    def wait(self, run_id, states, timeout=10):
        end = time.time() + timeout
        while time.time() < end:
            if self.app.status(run_id) in states:
                return self.app.status(run_id)
            time.sleep(0.05)
        self.fail(f"{run_id} stuck in {self.app.status(run_id)}")

    def test_approve_releases(self):
        rid = self.submit("case_002")
        self.wait(rid, {"AWAITING_APPROVAL"})
        self.assertEqual(self.get(f"/run/{rid}/report.md")[0], 404)  # nothing exposed before review
        self.assertEqual(self.post(f"/run/{rid}/decision", decision="approved", reviewer="qa")[0], 303)
        self.assertEqual(self.wait(rid, {"COMPLETED"}), "COMPLETED")
        self.assertTrue(list((self.app.runs_dir / rid / "outbox").glob("*.json")))
        state = json.loads((self.app.runs_dir / rid / "state.json").read_text())
        self.assertEqual(state["facts"]["approval"]["mode"], "web")
        self.assertIn("Human decision", self.get(f"/run/{rid}")[1])

    def test_reject_withholds(self):
        rid = self.submit("case_007")  # contains a prompt injection
        self.wait(rid, {"AWAITING_APPROVAL"})
        self.post(f"/run/{rid}/decision", decision="rejected", reviewer="qa")
        self.assertEqual(self.wait(rid, {"REJECTED_BY_HUMAN"}), "REJECTED_BY_HUMAN")
        self.assertFalse((self.app.runs_dir / rid / "outbox").exists())

    def test_timeout_leaves_pending(self):
        rid = self.submit("case_001")
        self.assertEqual(self.wait(rid, {"PENDING_APPROVAL"}, timeout=10), "PENDING_APPROVAL")
        self.assertFalse((self.app.runs_dir / rid / "outbox").exists())

    def test_routine_needs_no_review(self):
        self.assertEqual(self.wait(self.submit("case_003"), {"COMPLETED"}), "COMPLETED")

    def test_hostile_input(self):
        evil = "Case ID: ../../../../tmp/pwn\nPatient: 40 years, male\nReporter: doctor\nSuspect drug: Painex\nEvent: <script>alert(1)</script> headache\n"
        code, headers, _ = self.post("/run", report=evil)
        rid = headers["Location"].rsplit("/", 1)[1]
        self.wait(rid, {"AWAITING_APPROVAL", "COMPLETED", "PENDING_APPROVAL"})
        self.post(f"/run/{rid}/decision", decision="approved", reviewer="<b>x</b>")
        self.wait(rid, {"COMPLETED"})
        outbox = list((self.app.runs_dir / rid / "outbox").glob("*.json"))
        self.assertEqual(len(outbox), 1)
        self.assertNotIn("..", outbox[0].name)
        self.assertNotIn("<script>", self.get(f"/run/{rid}")[1])

    def test_routes_and_limits(self):
        self.assertEqual(self.get("/healthz")[0], 200)
        self.assertEqual(self.get("/dashboard")[0], 200)
        self.assertEqual(self.get("/run/web-../../etc/passwd")[0], 404)
        self.assertEqual(self.get("/run/web-000000000000/state.json")[0], 404)
        self.assertEqual(self.post("/run", report="")[0], 400)
        self.assertEqual(self.post("/run", report="x" * 30000)[0], 413)
        self.assertIn("runs", json.loads(self.get("/api/metrics")[1])["totals"])

    def test_token_required_when_configured(self):
        self.app.token = "s3cret"
        try:
            rid = self.submit("case_002")
            self.wait(rid, {"AWAITING_APPROVAL"})
            self.assertEqual(self.post(f"/run/{rid}/decision", decision="approved", reviewer="a", token="wrong")[0], 403)
            self.assertEqual(self.app.status(rid), "AWAITING_APPROVAL")
            self.post(f"/run/{rid}/decision", decision="approved", reviewer="a", token="s3cret")
            self.wait(rid, {"COMPLETED"})
        finally:
            self.app.token = None


if __name__ == "__main__":
    unittest.main()
