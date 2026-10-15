"""Exercise publication orchestration using local bare remotes and a recording gh fixture."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from test_runtime import Fixture, SCRIPTS, git


class AutomationTests(Fixture):
    def setUp(self):
        super().setUp()
        self.remote = self.root / "remote.git"
        subprocess.run(["git", "clone", "--quiet", "--bare", str(self.workspace), str(self.remote)], check=True)
        git(self.workspace, "remote", "add", "origin", str(self.remote))
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.gh_log = self.root / "gh.jsonl"
        gh = self.bin / "gh"
        gh.write_text(f"#!{sys.executable}\n" + '''import json,os,pathlib,sys
with open(os.environ["GH_LOG"],"a") as stream:
    stream.write(json.dumps(sys.argv[1:])+"\\n")
if sys.argv[1:3] == ["pr","list"]:
    print("[]")
elif sys.argv[1:3] == ["pr","create"]:
    assert pathlib.Path(sys.argv[sys.argv.index("--body-file")+1]).read_text().count("\\n") > 1
''')
        gh.chmod(0o755)
        self.env.update({"PATH": str(self.bin) + os.pathsep + self.env["PATH"],
                         "GH_LOG":str(self.gh_log),"SDLC_AGENT_ADAPTER":"command","GH_TOKEN":"fixture-not-a-secret"})
        self.adapter.write_text('''import json, os, pathlib, sys
request=json.load(sys.stdin)
assert "GH_TOKEN" not in os.environ and "GITHUB_TOKEN" not in os.environ
if os.environ.get("ADAPTER_WRITE"):
    pathlib.Path("unexpected.py").write_text("unapproved mutation")
output=os.environ.get("ADAPTER_REPLY","A report with evidence")
print(json.dumps({"schema_version":1,"status":"success","is_error":False,"output":output}))
''')

    def commit_fixture(self):
        git(self.workspace,"add",".")
        git(self.workspace,"-c","user.name=Test","-c","user.email=test@example.com","commit","-qm","configuration")

    def execute(self, name, *args):
        return subprocess.run([sys.executable,str(SCRIPTS/name),*args],cwd=self.workspace,
                              env=self.env,capture_output=True,text=True)

    def test_spec_generation_preserves_checkout_and_opens_a_review_pr(self):
        path=self.workspace/"intent/0001-example"
        path.mkdir(parents=True)
        (path/"intent.md").write_text("---\nstatus: draft\n---\n# Intent\n")
        self.commit_fixture()
        before=git(self.workspace,"rev-parse","HEAD")
        self.env["CHANGE"]="intent/0001-example"
        self.env["ADAPTER_REPLY"]="---\nstatus: draft\n---\n# Spec\n## Requirements\nR1\n## Design\nDesign\n## Areas of concern\nNone\n"
        process=self.execute("write_specs.py")
        self.assertEqual(process.returncode,0,process.stderr)
        self.assertFalse((path/"spec.md").exists())
        self.assertEqual(git(self.workspace,"rev-parse","HEAD"),before)
        self.assertIn("status: draft",(path/"intent.md").read_text())
        published=git(self.remote,"show","refs/heads/spec/0001-example:intent/0001-example/spec.md")
        self.assertIn("## Requirements",published)
        self.assertIn('"create"',self.gh_log.read_text())

    def test_spec_rejects_invalid_path_and_self_approval(self):
        self.env["CHANGE"]="intent/../../outside"
        self.assertNotEqual(self.execute("write_specs.py").returncode,0)
        path=self.workspace/"intent/0001-example"; path.mkdir(parents=True)
        (path/"intent.md").write_text("---\nstatus: draft\n---\n# Intent\n")
        self.commit_fixture(); self.env["CHANGE"]="intent/0001-example"
        self.env["ADAPTER_REPLY"]="---\nstatus: approved\n---\n## Requirements\n## Design\n## Areas of concern\n"
        self.assertNotEqual(self.execute("write_specs.py").returncode,0)
        self.assertFalse(self.gh_log.exists())

    def prepare_monitor(self):
        directory=self.workspace/"monitoring"; directory.mkdir()
        (directory/"bands.yaml").write_text('''metrics:
  - name: cycle_time
    tiers:
      3sigma: {action: report, mode: read-only}
runbooks: {}
''')
        (self.workspace/"intent").mkdir()
        self.commit_fixture()
        payload={"findings":[{"metric":"cycle_time","tier":"3sigma","action":"report",
                              "mode":"workspace-write","routes":["runbook:unapproved"]}]}
        findings=self.root/"findings.json"; findings.write_text(json.dumps(payload))
        return findings

    def test_monitor_permissions_and_routes_come_from_trusted_bands(self):
        findings=self.prepare_monitor()
        before=git(self.workspace,"rev-parse","HEAD")
        process=self.execute("respond.py",str(findings))
        self.assertEqual(process.returncode,0,process.stderr)
        self.assertEqual(git(self.workspace,"rev-parse","HEAD"),before)
        self.assertEqual(git(self.workspace,"status","--porcelain"),"")
        calls=[json.loads(line) for line in self.gh_log.read_text().splitlines()]
        self.assertTrue(any(c[:2]==["pr","create"] for c in calls))
        self.assertFalse(any(c[:2]==["workflow","run"] for c in calls))

    def test_monitor_refuses_read_only_mutation_before_publication(self):
        findings=self.prepare_monitor(); self.env["ADAPTER_WRITE"]="1"
        self.assertNotEqual(self.execute("respond.py",str(findings)).returncode,0)
        self.assertNotIn('"create"',self.gh_log.read_text())
        self.assertFalse((self.workspace/"unexpected.py").exists())

    def test_unknown_metric_and_escalated_tier_fail_before_external_operations(self):
        module_spec=importlib.util.spec_from_file_location("respond",SCRIPTS/"respond.py")
        module=importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
        config={"metrics":[{"name":"known","tiers":{"3sigma":{"action":"report","mode":"workspace-write"}}}]}
        for metric in ("unknown","known"):
            with self.subTest(metric=metric):
                with self.assertRaises(ValueError):
                    module.response_policy({"findings":[{"metric":metric,"tier":"3sigma","action":"report"}]},config)
