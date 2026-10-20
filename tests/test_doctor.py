"""Read-only fixture tests. Run with python3 -m unittest discover -s tests -v."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = ROOT / 'scripts/bash/doctor.sh'
ENGINE = ROOT / 'scripts/doctor.py'
SCRIPTS = ('common', 'check-prerequisites', 'create-new-feature', 'setup-plan', 'setup-tasks', 'resolve-template')

class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='doctor fixture ')
        self.project = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def write(self, path, text='fixture\n'):
        file = self.project / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding='utf-8')
        return file

    def layout(self, legacy=False, family='bash'):
        (self.project / '.specify').mkdir(exist_ok=True)
        prefix = '' if legacy else '.specify/'
        for directory in ('scripts', 'templates', 'memory'):
            (self.project / (prefix + directory)).mkdir(parents=True, exist_ok=True)
        self.write(prefix + 'memory/constitution.md')
        for script in SCRIPTS + (('update-agent-context',) if legacy else ()):
            file = self.write(prefix + 'scripts/' + family + '/' + script + ('.sh' if family == 'bash' else '.ps1'))
            file.chmod(0o755)
        self.write('.agents/skills/speckit-specify/SKILL.md')
        self.write('specs/001-feature/spec.md')
        self.write('.specify/extensions/.registry', '{"schema_version":"1.0","extensions":{}}')

    def run_doctor(self, *args, code=0, interpreter=None):
        env = dict(os.environ, PYTHON=interpreter or sys.executable, PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run(['bash', str(BASH), *args], cwd=self.project, env=env, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def test_current_layout_codex_skills_and_current_registry(self):
        self.layout()
        result = self.run_doctor('--json')
        value = json.loads(result.stdout)
        self.assertFalse((self.project / '.specify/scripts/bash/update-agent-context.sh').exists())
        self.assertEqual(value['errors'], 0)
        self.assertEqual(value['warnings'], 0)
        self.assertTrue(any('Codex' in finding['message'] for finding in value['findings']))
        self.assertFalse(any('Amp' in finding['message'] for finding in value['findings']))
        self.assertTrue(any('.registry' in finding['message'] for finding in value['findings']))
        self.assertEqual(result.stderr, '')

    def test_legacy_layout_and_registry_remain_supported(self):
        self.layout(legacy=True)
        (self.project / '.specify/extensions/.registry').rename(self.project / '.specify/extensions/registry.json')
        (self.project / '.agents').rename(self.project / 'agent-backup')
        self.write('.codex/prompts/speckit.specify.md')
        result = json.loads(self.run_doctor('--json').stdout)
        self.assertEqual(result['errors'], 0)
        self.assertTrue(any('legacy' in finding['message'].lower() for finding in result['findings']))

    def test_powershell_only_project_is_not_missing_bash(self):
        self.layout(family='powershell')
        self.assertEqual(json.loads(self.run_doctor('--json').stdout)['errors'], 0)

    def test_missing_selected_scripts_and_missing_specs_are_distinct(self):
        self.layout()
        (self.project / '.specify/scripts/bash/setup-plan.sh').unlink()
        shutil.rmtree(self.project / 'specs')
        value = json.loads(self.run_doctor('--json', code=1).stdout)
        self.assertEqual(value['errors'], 1)
        self.assertTrue(any('specs/' in finding['message'] and finding['severity'] == 'note' for finding in value['findings']))

    def test_json_escapes_names_and_contains_no_human_prefix(self):
        self.layout()
        self.write('specs/003-a "quoted" feature/spec.md')
        value = json.loads(self.run_doctor('--json').stdout)
        self.assertTrue(any('a "quoted" feature' in finding['message'] for finding in value['findings']))

    def test_malformed_registry_is_an_error_not_installed_proof(self):
        self.layout()
        self.write('.specify/extensions/.registry', '{not JSON')
        value = json.loads(self.run_doctor('--json', code=1).stdout)
        self.assertEqual(value['errors'], 1)
        for invalid in ('{"extensions":[]}', '{"extensions":{"example":{"enabled":"yes"}}}'):
            self.write('.specify/extensions/.registry', invalid)
            self.assertGreater(json.loads(self.run_doctor('--json', code=1).stdout)['errors'], 0)

    def test_malformed_yaml_is_reported_with_parser_available(self):
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest('PyYAML is optional; run this fixture with PyYAML installed')
        self.layout()
        self.write('.specify/extensions.yml', 'hooks: [unterminated')
        value = json.loads(self.run_doctor('--json', code=1).stdout)
        self.assertTrue(any('YAML' in finding['message'] for finding in value['findings']))

    def test_unavailable_yaml_validation_is_explicit(self):
        self.layout()
        self.write('.specify/extensions.yml', 'hooks: {}\n')
        result = subprocess.run([sys.executable, '-S', str(ENGINE), '--json'], cwd=self.project, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertTrue(any('not validated' in finding['message'] and finding['severity'] == 'warning' for finding in value['findings']))

    def test_no_project_files_created_or_modified(self):
        self.layout()
        def snapshot():
            return {str(path.relative_to(self.project)): (path.stat().st_mode, path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None) for path in self.project.rglob('*')}
        before = snapshot()
        self.run_doctor('--json')
        self.assertEqual(snapshot(), before)

    def test_readonly_project_can_emit_json(self):
        if os.name == 'nt':
            self.skipTest('POSIX mode fixture')
        self.layout()
        paths = list(self.project.rglob('*'))
        for path in paths:
            path.chmod(0o555 if path.is_dir() or path.suffix == '.sh' else 0o444)
        self.project.chmod(0o555)
        try:
            self.assertEqual(json.loads(self.run_doctor('--json').stdout)['errors'], 0)
        finally:
            self.project.chmod(0o755)
            for path in paths:
                path.chmod(0o755 if path.is_dir() else 0o644)

    def test_help_and_unknown_arguments(self):
        self.assertIn('--json', self.run_doctor('--help').stdout)
        self.assertEqual(self.run_doctor('--fix', code=2).stdout, '')

    @unittest.skipUnless(shutil.which('pwsh'), 'PowerShell runtime unavailable')
    def test_powershell_wrapper_matches_bash_json(self):
        self.layout()
        expected = json.loads(self.run_doctor('--json').stdout)
        result = subprocess.run(['pwsh', '-NoProfile', '-File', str(ROOT / 'scripts/powershell/doctor.ps1'), '-Json'], cwd=self.project, env=dict(os.environ, PYTHON=sys.executable), text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), expected)

if __name__ == '__main__':
    unittest.main()
