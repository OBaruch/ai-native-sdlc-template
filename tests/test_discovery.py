"""Ensure portable role/command metadata translates to native discovery semantics."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import yaml

SCRIPT = Path(__file__).resolve().parent.parent / "scripts/sync_adapters.py"
SPEC = importlib.util.spec_from_file_location("sync_adapters", SCRIPT)
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "instructions.md"

    def test_read_only_role_exposes_no_native_write_tool(self):
        self.path.write_text("---\nname: observer\ndescription: Report only\ncapabilities: [read, search]\n---\nDo not edit.\n")
        generated = SYNC.claude_content(self.path, "roles")
        metadata = yaml.safe_load(generated.split("---", 2)[1])
        self.assertEqual(set(metadata["tools"].split(", ")), {"Read", "Grep", "Glob"})
        self.assertNotIn("capabilities", metadata)
        self.assertTrue(generated.endswith("Do not edit.\n"))

    def test_unknown_capability_fails_instead_of_expanding_permissions(self):
        self.path.write_text("---\nname: observer\ndescription: Report only\ncapabilities: [unrestricted]\n---\nReport.\n")
        with self.assertRaises(ValueError):
            SYNC.claude_content(self.path, "roles")

    def test_portable_arguments_translate_without_changing_canonical_content(self):
        text = "---\ndescription: Draft\nargument: <intent folder>\n---\nRead {{arguments}}/intent.md.\n"
        self.path.write_text(text)
        generated = SYNC.claude_content(self.path, "commands")
        self.assertIn("argument-hint: <intent folder>", generated)
        self.assertIn("Read $ARGUMENTS/intent.md.", generated)
        self.assertEqual(self.path.read_text(), text)
