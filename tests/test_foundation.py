"""Positive and negative tests of the foundation checker, not product tests."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.check_foundation import IGNORED, REQUIRED, check_content, check_git


class ContentChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for relative in REQUIRED:
            self.write(relative, "# Fixture\n")
        self.write(".env.example", "# Empty by design\nXGLASSES_USB_PORT=\n")
        self.write("requirements-dev.txt", "ruff==0.12.12\n")

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_valid_foundation(self):
        self.assertEqual(check_content(self.root), [])

    def test_missing_required_file(self):
        (self.root / "AGENTS.md").unlink()
        self.assertIn("missing file: AGENTS.md", check_content(self.root))

    def test_empty_required_file(self):
        self.write("README.md", " \n")
        self.assertIn("empty file: README.md", check_content(self.root))

    def test_conflict_marker(self):
        self.write("README.md", "# Header\n<<<<<<< HEAD\nconflict\n")
        self.assertIn("conflict marker: README.md", check_content(self.root))

    def test_env_value_rejected_without_leaking_value(self):
        self.write(".env.example", "XGLASSES_DIALOG_API_KEY=private-fixture-value\n")
        errors = check_content(self.root)
        self.assertTrue(any("placeholder" in error for error in errors))
        self.assertNotIn("private-fixture-value", " ".join(errors))

    def test_malformed_env_rejected(self):
        self.write(".env.example", "missing_equals\n")
        self.assertTrue(any("placeholder" in error for error in check_content(self.root)))

    def test_heavy_or_floating_dependency_rejected(self):
        for dependencies in ("ruff>=0.12\n", "ruff==0.12.12\ntorch==2.0\n"):
            with self.subTest(dependencies=dependencies):
                self.write("requirements-dev.txt", dependencies)
                self.assertTrue(any("dependencies" in e for e in check_content(self.root)))

    def test_premature_runtime_rejected(self):
        self.write("server/main.py", "# Premature runtime\n")
        self.assertTrue(any("runtime file" in e for e in check_content(self.root)))

    def test_broken_relative_link(self):
        self.write("README.md", "[missing](docs/missing.md)\n")
        self.assertTrue(any("local link" in e for e in check_content(self.root)))

    def test_valid_links_and_external_urls(self):
        self.write("README.md", "[local](AGENTS.md) [web](https://example.invalid) [anchor](#a)\n")
        self.assertEqual(check_content(self.root), [])


class GitChecks(unittest.TestCase):
    def test_git_not_installed(self):
        with patch("tools.check_foundation.subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual(check_git(Path.cwd()), ["Git unavailable or timed out"])

    def test_not_a_repository(self):
        result = subprocess.CompletedProcess([], 128, "", "not a repository")
        with patch("tools.check_foundation.subprocess.run", return_value=result):
            self.assertEqual(check_git(Path.cwd()), ["project root is not the Git worktree root"])

    def test_ignore_rule_mismatch(self):
        root = Path.cwd()
        responses = [subprocess.CompletedProcess([], 0, str(root), "")]
        responses += [subprocess.CompletedProcess([], 1, "", "")] * (len(IGNORED) + 1)
        with patch("tools.check_foundation.subprocess.run", side_effect=responses):
            self.assertTrue(any("ignore rule" in e for e in check_git(root)))


if __name__ == "__main__":
    unittest.main()
