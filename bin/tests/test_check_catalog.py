#!/usr/bin/env python
"""The catalog checker has to actually reject bad catalogs.

A validator that passes everything is worse than no validator, because a green
run implies it checked. Each case here plants one specific defect and asserts
the checker fails on it.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "bin" / "check-catalog.py"

VALID = {
    "name": "someone",
    "owner": {"name": "Someone"},
    "plugins": [{
        "name": "a-plugin",
        "source": {"source": "github", "repo": "someone/a-plugin"},
        "description": "Does a thing.",
        "version": "1.0.0",
    }],
}


def run_against(catalog):
    """Run the checker against a temp repo holding this catalog. Returns (rc, out)."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / ".claude-plugin").mkdir()
        (td / "bin").mkdir()
        (td / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps(catalog) if not isinstance(catalog, str) else catalog,
            encoding="utf-8")
        # The checker resolves the catalog relative to its own parents[1].
        shim = td / "bin" / "check-catalog.py"
        shim.write_text(CHECKER.read_text(encoding="utf-8"), encoding="utf-8")
        p = subprocess.run([sys.executable, str(shim)], capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr


def mutate(**changes):
    c = json.loads(json.dumps(VALID))
    c.update(changes)
    return c


def with_plugin(**changes):
    c = json.loads(json.dumps(VALID))
    c["plugins"][0].update(changes)
    return c


class CatalogChecker(unittest.TestCase):

    def test_valid_catalog_passes(self):
        rc, out = run_against(VALID)
        self.assertEqual(rc, 0, out)

    def test_malformed_json_fails(self):
        rc, out = run_against("{not json")
        self.assertEqual(rc, 1)
        self.assertIn("not valid JSON", out)

    def test_reserved_marketplace_name_fails(self):
        rc, out = run_against(mutate(name="claude-community"))
        self.assertEqual(rc, 1)
        self.assertIn("reserved", out)

    def test_impersonating_name_fails(self):
        rc, out = run_against(mutate(name="official-claude-plugins"))
        self.assertEqual(rc, 1)
        self.assertIn("impersonates", out)

    def test_non_kebab_marketplace_name_fails(self):
        rc, out = run_against(mutate(name="My Marketplace"))
        self.assertEqual(rc, 1)
        self.assertIn("kebab-case", out)

    def test_missing_owner_fails(self):
        c = mutate()
        del c["owner"]
        rc, out = run_against(c)
        self.assertEqual(rc, 1)
        self.assertIn("owner.name", out)

    def test_duplicate_plugin_names_fail(self):
        c = mutate()
        c["plugins"] = c["plugins"] + json.loads(json.dumps(c["plugins"]))
        rc, out = run_against(c)
        self.assertEqual(rc, 1)
        self.assertIn("duplicate", out)

    def test_non_kebab_plugin_name_fails(self):
        rc, out = run_against(with_plugin(name="My_Plugin"))
        self.assertEqual(rc, 1)
        self.assertIn("kebab-case", out)

    def test_unknown_source_type_fails(self):
        rc, out = run_against(with_plugin(source={"source": "ftp", "url": "x"}))
        self.assertEqual(rc, 1)
        self.assertIn("unknown source type", out)

    def test_github_source_without_repo_fails(self):
        rc, out = run_against(with_plugin(source={"source": "github"}))
        self.assertEqual(rc, 1)
        self.assertIn("requires `repo`", out)

    def test_github_repo_without_owner_fails(self):
        rc, out = run_against(with_plugin(source={"source": "github", "repo": "noowner"}))
        self.assertEqual(rc, 1)
        self.assertIn("owner/name", out)

    def test_local_source_must_exist(self):
        rc, out = run_against(with_plugin(source="./plugins/nope"))
        self.assertEqual(rc, 1)
        self.assertIn("does not exist", out)

    def test_missing_version_warns_but_passes(self):
        c = with_plugin()
        del c["plugins"][0]["version"]
        rc, out = run_against(c)
        self.assertEqual(rc, 0, out)
        self.assertIn("no `version`", out)


if __name__ == "__main__":
    unittest.main()
