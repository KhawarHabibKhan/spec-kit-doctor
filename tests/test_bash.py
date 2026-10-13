import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/bash/doctor.sh"

class DoctorTests(unittest.TestCase):
    def test_modern_layout_codex_skills_and_json_stdout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in (".specify/templates", ".specify/memory", ".specify/extensions", ".agents/skills/speckit-specify", "specs"):
                (root / name).mkdir(parents=True)
            (root / ".specify/memory/constitution.md").write_text("# Principles")
            (root / ".agents/skills/speckit-specify/SKILL.md").write_text("# Specify")
            (root / ".specify/extensions/.registry").write_text('{"extensions":{}}')
            scripts = root / ".specify/scripts/bash"
            scripts.mkdir(parents=True)
            for name in ("common", "check-prerequisites", "create-new-feature", "setup-plan", "setup-tasks", "resolve-template"):
                path = scripts / (name + ".sh")
                path.write_text("#!/bin/sh\nexit 0\n")
                path.chmod(0o755)
            result = subprocess.run(["bash", str(SCRIPT), "--json"], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["errors"], 0)
            self.assertEqual(json.loads(result.stdout)["warnings"], 0)
            self.assertIn("Codex CLI (skills", result.stderr)
            self.assertIn("Extension registry found", result.stderr)
            (scripts / "common.sh").unlink()
            result = subprocess.run(["bash", str(SCRIPT), "--json"], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertGreater(json.loads(result.stdout)["errors"], 0)
