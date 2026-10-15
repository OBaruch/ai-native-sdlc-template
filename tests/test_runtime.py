"""Offline contract and integration tests; no provider key or model call is used."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "repo"
        self.workspace.mkdir()
        (self.workspace / "AGENTS.md").write_text("Canonical test instructions.\n")
        (self.workspace / ".gitignore").write_text("evals/.runs/\n.agents/verification.json\n")
        git(self.workspace, "init", "-q")
        git(self.workspace, "add", ".")
        git(self.workspace, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "fixture")
        self.prompt = self.root / "prompt.md"
        self.prompt.write_text("Test task with literal $(touch unwanted) and `commands`.")
        self.output = self.root / "output.json"
        self.adapter = self.root / "adapter.py"
        self.adapter.write_text('''import json, os, pathlib, sys
r = json.load(sys.stdin)
assert r["schema_version"] == 1 and "Canonical test instructions" in r["prompt"]
assert r["instructions"]["skills"] == ".agents/skills"
if os.environ.get("CAPTURE"):
    pathlib.Path(os.environ["CAPTURE"]).write_text(json.dumps(r))
if os.environ.get("ADAPTER_WRITE"):
    pathlib.Path("result.txt").write_text("isolated change")
behavior = os.environ.get("BEHAVIOR", "success")
if behavior == "exit":
    sys.exit(7)
if behavior == "malformed":
    print("not json")
elif behavior == "inconsistent":
    print(json.dumps({"schema_version": 1, "status": "success", "is_error": True, "output": "wrong"}))
elif behavior == "empty":
    pass
else:
    error = behavior == "error"
    print(json.dumps({"schema_version": 1, "status": "error" if error else "success", "is_error": error, "output": "reply"}))
''')
        self.env = {**os.environ, "SDLC_AGENT_COMMAND": json.dumps([sys.executable, str(self.adapter)]),
                    "SDLC_AGENT_MODES": "read-only,workspace-write"}
        self.env.pop("SDLC_AGENT_ADAPTER", None)

    def run_agent(self, adapter="command", mode="read-only", timeout=10):
        return subprocess.run([sys.executable, str(SCRIPTS / "agent_run.py"), "--adapter", adapter,
            "--workspace", str(self.workspace), "--prompt-file", str(self.prompt), "--output", str(self.output),
            "--mode", mode, "--timeout", str(timeout)], env=self.env, capture_output=True, text=True)

    def policy(self, operation=None, phase="before", raw=None):
        event = {"schema_version": 1, "phase": phase, "operation": operation or {"kind": "none"}}
        process = subprocess.run([sys.executable, str(SCRIPTS / "policy.py"), "--project", str(self.workspace)],
            input=raw if raw is not None else json.dumps(event), env=self.env, capture_output=True, text=True)
        return process, json.loads(process.stdout)


class RunnerTests(Fixture):
    def test_generic_request_includes_instructions_and_literal_prompt(self):
        capture = self.root / "request.json"
        self.env["CAPTURE"] = str(capture)
        process = self.run_agent()
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(self.output.read_text())["status"], "success")
        self.assertIn("$(touch unwanted)", json.loads(capture.read_text())["prompt"])
        self.assertFalse((self.workspace / "unwanted").exists())

    def test_command_mode_requires_explicit_capability(self):
        self.env["SDLC_AGENT_MODES"] = "read-only"
        self.assertNotEqual(self.run_agent(mode="workspace-write").returncode, 0)
        self.assertIn("has not declared", self.output.read_text())

    def test_protocol_failures_are_never_success(self):
        for behavior in ("malformed", "inconsistent", "empty", "error", "exit"):
            with self.subTest(behavior=behavior):
                self.env["BEHAVIOR"] = behavior
                self.assertNotEqual(self.run_agent().returncode, 0)
                self.assertTrue(json.loads(self.output.read_text())["is_error"])

    def test_no_implicit_provider(self):
        process = subprocess.run([sys.executable, str(SCRIPTS / "agent_run.py"), "--prompt-file", str(self.prompt),
            "--output", str(self.output)], env=self.env, capture_output=True)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("no default provider", self.output.read_text())

    def test_missing_executable_and_invalid_argv(self):
        for command in ('"shell command"', '["/nonexistent/harness"]', '[]'):
            with self.subTest(command=command):
                self.env["SDLC_AGENT_COMMAND"] = command
                self.assertNotEqual(self.run_agent().returncode, 0)

    def test_bundled_stdin_shim_needs_no_vendor_specific_code(self):
        shim = ROOT / ".agents/adapters/stdin_cli.py"
        self.env["SDLC_AGENT_COMMAND"] = json.dumps([sys.executable, str(shim)])
        self.env["SDLC_HARNESS_MODE_COMMANDS"] = json.dumps({"read-only": [sys.executable, "-c", "import sys; print('reviewed: '+sys.stdin.read())"]})
        self.assertEqual(self.run_agent().returncode, 0)
        self.assertIn("Canonical test instructions", json.loads(self.output.read_text())["output"])
        self.assertNotEqual(self.run_agent(mode="workspace-write").returncode, 0)

    def test_native_claude_and_codex_translation(self):
        binaries = self.root / "bin"
        binaries.mkdir()
        capture = self.root / "native.json"
        self.env["CAPTURE"] = str(capture)
        self.env["PATH"] = str(binaries) + os.pathsep + self.env["PATH"]
        for adapter in ("claude", "codex"):
            binary = binaries / adapter
            binary.write_text(f"#!{sys.executable}\n" + '''import json, os, pathlib, sys
prompt = sys.stdin.read()
pathlib.Path(os.environ["CAPTURE"]).write_text(json.dumps({"args":sys.argv[1:],"prompt":prompt}))
if pathlib.Path(sys.argv[0]).name == "claude":
    print(json.dumps({"is_error":False,"result":"native reply"}))
else:
    pathlib.Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text("native reply")
''')
            binary.chmod(0o755)
            for mode in ("read-only", "workspace-write"):
                with self.subTest(adapter=adapter, mode=mode):
                    self.assertEqual(self.run_agent(adapter=adapter, mode=mode).returncode, 0)
                    data = json.loads(capture.read_text())
                    self.assertIn("Canonical test instructions", data["prompt"])
                    self.assertEqual(json.loads(self.output.read_text())["output"], "native reply")
                    if adapter == "codex":
                        self.assertIn("mcp_servers={}", data["args"])
                        self.assertEqual(data["args"][data["args"].index("--sandbox")+1], mode)
                        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", data["args"])
                    else:
                        self.assertIn("--strict-mcp-config", data["args"])
                        self.assertIn('{"mcpServers":{}}', data["args"])
                        tools = data["args"][data["args"].index("--tools")+1]
                        self.assertEqual("Write" in tools, mode == "workspace-write")

    def test_timeout_stops_child_tools(self):
        marker = self.root / "escaped-child"
        child = "import pathlib,time; time.sleep(2); pathlib.Path(" + repr(str(marker)) + ").touch()"
        self.adapter.write_text("import subprocess,sys,time\nsubprocess.Popen([sys.executable,'-c'," + repr(child) + "])\ntime.sleep(30)\n")
        self.assertNotEqual(self.run_agent(timeout=1).returncode, 0)
        time.sleep(1.3)
        self.assertFalse(marker.exists())


class PolicyTests(Fixture):
    def test_production_gate_is_harness_independent(self):
        operation = {"kind": "shell", "command": "./scripts/deploy.sh production"}
        self.env.pop("RELEASE_APPROVAL", None)
        self.assertEqual(self.policy(operation)[1]["decision"], "deny")
        self.env["RELEASE_APPROVAL"] = "CHG-123"
        self.assertEqual(self.policy(operation)[1]["decision"], "allow")

    def test_generated_secret_and_guardrail_paths(self):
        for path, expected in (("src/gen/x.py", "deny"), (".env", "deny"), (".agents/hooks/lib.sh", "ask"), ("src/app.py", "allow")):
            with self.subTest(path=path):
                process, result = self.policy({"kind": "write", "path": path, "content": "safe"})
                self.assertEqual(result["decision"], expected)
                self.assertEqual(process.returncode, 0 if expected == "allow" else 2)

    def test_secret_reads_denied(self):
        self.assertEqual(self.policy({"kind": "read", "path": ".env"})[1]["decision"], "deny")

    def test_fix_task_uses_neutral_marker(self):
        (self.workspace / ".agents").mkdir()
        (self.workspace / ".agents/fix-task").touch()
        self.assertEqual(self.policy({"kind": "write", "path": "tests/test_app.py"})[1]["decision"], "deny")
        self.assertEqual(self.policy({"kind": "shell", "command": "make test"})[1]["decision"], "allow")

    def test_invalid_events_fail_closed(self):
        for raw in ("not json", "[]", '{}', '{"schema_version":true}', '{"schema_version":1,"phase":"before","operation":{"kind":"shell"}}',
                    '{"schema_version":1,"phase":[],"operation":{"kind":"none"}}',
                    '{"schema_version":1,"phase":"before","operation":{"kind":[]}}',
                    '{"schema_version":1,"phase":"finish","operation":{"kind":"none"},"approved":true}'):
            with self.subTest(raw=raw):
                self.assertEqual(self.policy(raw=raw)[1]["decision"], "deny")

    def test_path_traversal_cannot_bypass_generated_protection(self):
        self.assertEqual(self.policy({"kind": "write", "path": "src/../src/gen/x.py"})[1]["decision"], "deny")

    def test_verification_expires_after_any_content_change(self):
        module_spec = importlib.util.spec_from_file_location("verify", SCRIPTS / "verify.py")
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        (self.workspace / "source.py").write_text("before")
        (self.workspace / ".agents").mkdir()
        self.assertFalse(module.check(self.workspace))
        receipt = self.workspace / ".agents/verification.json"
        receipt.write_text(json.dumps({"passed": True, "fingerprint": module.fingerprint(self.workspace)}))
        self.assertTrue(module.check(self.workspace))
        (self.workspace / "source.py").write_text("after")
        self.assertFalse(module.check(self.workspace))


class EvalTests(Fixture):
    def setUp(self):
        super().setUp()
        (self.workspace / "evals").mkdir()
        self.env["SDLC_AGENT_ADAPTER"] = "command"

    def write_case(self, case_id="case", checks=None, enabled=True):
        case = {"id":case_id,"enabled":enabled,"prompt":"make a change","mode":"workspace-write",
                "checks":checks or [{"result_field":"is_error","equals":False}]}
        (self.workspace / "evals" / f"{case_id}.json").write_text(json.dumps(case))

    def run_evals(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "run_evals.py"), *args], cwd=self.workspace,
                              env=self.env, text=True, capture_output=True)

    def test_evaluation_modifies_only_disposable_clone(self):
        self.write_case(checks=[{"run":"test -f result.txt"},{"result_field":"is_error","equals":False}])
        self.env["ADAPTER_WRITE"] = "1"
        before = git(self.workspace, "status", "--porcelain")
        process = self.run_evals()
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertFalse((self.workspace / "result.txt").exists())
        self.assertEqual(git(self.workspace,"status","--porcelain"), before)
        self.assertEqual(git(self.workspace,"worktree","list","--porcelain").count("worktree "), 1)
        report = json.loads(next((self.workspace / "evals/.runs").glob("*/summary.json")).read_text())
        self.assertEqual((report["passed"],report["total"]), (1,1))

    def test_disabled_cases_are_skipped_and_required_suite_fails(self):
        self.write_case(enabled=False)
        self.assertEqual(self.run_evals().returncode, 0)
        process = self.run_evals("--require-enabled")
        self.assertEqual(process.returncode, 2)
        self.assertIn("SKIPPED", process.stdout)

    def test_agent_exit_failure_cannot_pass_grading(self):
        self.write_case(checks=[{"run":"true"}])
        self.env["BEHAVIOR"]="exit"
        self.assertEqual(self.run_evals().returncode, 1)

    def test_threshold_uses_actual_rate_without_rounding(self):
        self.write_case("one")
        self.write_case("two")
        self.write_case("three", checks=[{"run":"false"}])
        self.env["EVAL_PASS_THRESHOLD"]="0.667"
        self.assertEqual(self.run_evals().returncode, 1)

    def test_invalid_threshold_and_case_id(self):
        for threshold in ("NaN", "1.1", "-0.1"):
            self.env["EVAL_PASS_THRESHOLD"]=threshold
            self.assertEqual(self.run_evals().returncode, 2)
        self.env.pop("EVAL_PASS_THRESHOLD")
        self.write_case()
        path=self.workspace / "evals/case.json"
        case=json.loads(path.read_text()); case["id"]="../unsafe"; path.write_text(json.dumps(case))
        self.assertEqual(self.run_evals().returncode, 2)


if __name__ == "__main__":
    unittest.main()
