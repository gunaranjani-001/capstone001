"""Tiny MCP client: spawns the stdio server and calls tools over JSON-RPC."""
import json
import subprocess
import sys

from .config import ROOT


class MCPError(RuntimeError):
    pass


class MCPClient:
    def __init__(self, cmd=None):
        self.proc = subprocess.Popen(
            cmd or [sys.executable, "-m", "pvagent.mcp_server"], cwd=ROOT,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self._id = 0
        self.rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                "clientInfo": {"name": "pv-triage", "version": "1.0.0"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def rpc(self, method, params=None):
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}})
        line = self.proc.stdout.readline()
        if not line:
            raise MCPError("MCP server closed the connection")
        resp = json.loads(line)
        if "error" in resp:
            raise MCPError(resp["error"]["message"])
        return resp["result"]

    def list_tools(self):
        return [t["name"] for t in self.rpc("tools/list")["tools"]]

    def call_tool(self, name, args):
        res = self.rpc("tools/call", {"name": name, "arguments": args})
        text = res["content"][0]["text"]
        if res.get("isError"):
            raise MCPError(text)
        return json.loads(text)

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=3)
        except Exception:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
