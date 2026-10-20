#!/usr/bin/env python3
"""Read-only Spec Kit diagnostics shared by Bash and PowerShell entrypoints."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import re
from project_state import project_root, native_state, resolve_feature

SCRIPT_NAMES = ('common', 'check-prerequisites', 'create-new-feature', 'setup-plan')
OPTIONAL_SCRIPT_NAMES = ('setup-tasks', 'resolve-template', 'update-agent-context')
# Current skill integrations and retained legacy command paths. Detect the actual
# command directory, never its parent (e.g. .agents is not proof of Amp).
AGENTS = {
    'Codex CLI': ('.agents/skills', '.codex/prompts'),
    'Claude Code': ('.claude/skills', '.claude/commands'),
    'GitHub Copilot': ('.github/skills', '.github/agents', '.github/prompts'),
    'Gemini CLI': ('.gemini/commands',),
    'Cursor': ('.cursor/skills', '.cursor/commands'),
    'Qwen Code': ('.qwen/commands',),
    'opencode': ('.opencode/command', '.opencode/commands'),
    'Windsurf': ('.windsurf/workflows',),
    'Kilo Code': ('.kilo/commands', '.kilocode/workflows'),
    'Auggie CLI': ('.augment/commands',),
    'CodeBuddy': ('.codebuddy/commands',),
    'Qoder CLI': ('.qoder/commands',),
    'Roo Code': ('.roo/commands',),
    'Kiro CLI': ('.kiro/prompts',),
    'Amp': ('.agents/commands',),
    'SHAI': ('.shai/commands',),
    'Tabnine CLI': ('.tabnine/agent/commands',),
    'Antigravity': ('.agent/skills', '.agent/workflows'),
    'IBM Bob': ('.bob/commands',),
    'Mistral Vibe': ('.vibe/prompts',),
    'Kimi Code': ('.kimi/skills',),
    'Alquimia AI': ('.alquimia/skills',),
    'Cline': ('.clinerules/workflows',),
    'Droid': ('.factory/skills',),
    'Firebender': ('.firebender/commands',),
    'Grok': ('.grok/skills',),
    'Junie': ('.junie/commands',),
    'Lingma': ('.lingma/skills',),
    'omp': ('.omp/commands',),
    'Pi': ('.pi/prompts',),
    'Trae': ('.trae/skills',),
    'Zcode': ('.zcode/skills',),
}


def diagnose(root):
    findings = []
    state, selector = native_state(root)
    active = resolve_feature(root, selector)

    def add(section, severity, message):
        findings.append({'section': section, 'severity': severity, 'message': message})

    def check(path, directory=True, severity='error'):
        exists = path.is_dir() if directory else path.is_file()
        label = path.relative_to(root).as_posix() + ('/' if directory else '')
        add('structure', 'ok' if exists else severity, label + (' found' if exists else ' is missing'))
        return exists

    check(root / '.specify')
    legacy = not any((root / '.specify' / name).exists() for name in ('scripts', 'templates', 'memory')) and all((root / name).is_dir() for name in ('scripts', 'templates', 'memory'))
    base = root if legacy else root / '.specify'
    if legacy:
        add('structure', 'note', 'Using legacy root-level scripts/templates/memory layout')
    for name in ('scripts', 'templates', 'memory'):
        check(base / name)
    check(base / 'memory/constitution.md', directory=False, severity='warning')
    check(root / 'specs', severity='note')

    detected = False
    for agent, paths in AGENTS.items():
        existing = [root / path for path in paths if (root / path).is_dir()]
        if not existing:
            continue
        detected = True
        valid = [path for path in existing if any(path.glob('speckit-*/SKILL.md')) or any(path.glob('speckit*.md'))]
        if valid:
            add('agents', 'ok', agent + ' Spec Kit commands/skills found in ' + ', '.join(path.relative_to(root).as_posix() for path in valid))
        else:
            add('agents', 'warning', agent + ' command directory exists but no Spec Kit command/skill manifests were found')
    if not detected:
        add('agents', 'note', 'No supported AI agent command directory detected')

    if (root / 'specs').is_dir():
        features = sorted(path for path in (root / 'specs').iterdir() if path.is_dir() and re.match(r'^[0-9]{3}-', path.name))
        if not features:
            add('features', 'note', 'No feature directories; create a specification when ready')
        for feature in features:
            if feature.is_symlink():
                add('features', 'error', 'Unsafe feature ' + feature.name)
                continue
            if not (feature / 'spec.md').is_file():
                add('features', 'error', 'Feature ' + repr(feature.name) + ' is missing spec.md')
            else:
                add('features', 'ok', 'Feature ' + repr(feature.name) + ' has spec.md')
                for name in ('plan', 'tasks'):
                    if not (feature / (name + '.md')).is_file():
                        add('features', 'note', 'Feature ' + repr(feature.name) + ' has no ' + name + '.md; use the corresponding Spec Kit command when ready')

    families = [(name, suffix) for name, suffix in (('bash', '.sh'), ('powershell', '.ps1')) if (base / 'scripts' / name).is_dir()]
    if not families and (base / 'scripts').is_dir():
        add('scripts', 'error', 'No supported Bash or PowerShell script family found')
    for family, suffix in families:
        for name in SCRIPT_NAMES + (('update-agent-context',) if legacy else ()):
            path = base / 'scripts' / family / (name + suffix)
            label = path.relative_to(root).as_posix()
            if not path.is_file():
                add('scripts', 'error', label + ' is missing')
            elif family == 'bash' and os.name != 'nt' and not os.access(path, os.X_OK):
                add('scripts', 'warning', label + ' is not executable')
            else:
                add('scripts', 'ok', label + ' found')
        for name in OPTIONAL_SCRIPT_NAMES:
            if legacy and name == 'update-agent-context':
                continue
            path = base / 'scripts' / family / (name + suffix)
            if path.is_file():
                add('scripts', 'ok', path.relative_to(root).as_posix() + ' optional/version-specific helper found')


    config = root / '.specify/extensions.yml'
    if config.is_file():
        try:
            if config.stat().st_size > 1_000_000:
                raise ValueError('size')
            try:
                import yaml
            except ImportError:
                add('extensions', 'warning', 'extensions.yml not validated: optional PyYAML parser is unavailable')
            else:
                try:
                    value = yaml.safe_load(config.read_text(encoding='utf-8'))
                except yaml.YAMLError:
                    raise ValueError('yaml') from None
                if not isinstance(value, dict) or ('hooks' in value and not isinstance(value['hooks'], dict)) or ('installed' in value and (not isinstance(value['installed'], list) or any(not isinstance(item, str) for item in value['installed']))):
                    raise ValueError('schema')
                add('extensions', 'ok', 'extensions.yml YAML and top-level configuration shapes validated')
        except (OSError, UnicodeError, ValueError):
            add('extensions', 'error', 'extensions.yml contains invalid/unreadable YAML or unsupported top-level configuration')
    else:
        add('extensions', 'note', 'No extensions.yml configuration found')

    current = root / '.specify/extensions/.registry'
    old = root / '.specify/extensions/registry.json'
    registry = current if current.is_file() else old if old.is_file() else None
    if registry:
        try:
            if registry.stat().st_size > 1_000_000:
                raise ValueError('size')
            data = json.loads(registry.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or not isinstance(data.get('extensions'), dict):
                raise ValueError('schema')
            for entry in data['extensions'].values():
                if not isinstance(entry, dict) or ('enabled' in entry and not isinstance(entry['enabled'], bool)) or ('version' in entry and not isinstance(entry['version'], str)):
                    raise ValueError('entry')
            label = registry.relative_to(root).as_posix()
            add('extensions', 'ok', label + ' JSON registry validated (' + str(len(data['extensions'])) + ' entries)')
            if registry == old:
                add('extensions', 'note', 'Using legacy registry.json extension registry')
            elif old.exists():
                add('extensions', 'warning', 'Both extension registries exist; current .registry takes precedence; legacy registry.json was not validated')
        except (OSError, UnicodeError, ValueError):
            add('extensions', 'error', registry.relative_to(root).as_posix() + ' contains invalid/unreadable JSON or unsupported registry shape')
    else:
        add('extensions', 'note', 'No installed extension registry found')

    if not shutil.which('git'):
        add('git', 'note', 'Git is not installed')
    else:
        try:
            environment = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
            result = subprocess.run(['git', '-C', str(root), 'rev-parse', '--is-inside-work-tree'], env=environment, capture_output=True, text=True, timeout=5)
            if result.returncode or result.stdout.strip() != 'true':
                add('git', 'note', 'Not inside a Git working tree')
            else:
                add('git', 'ok', 'Inside a Git working tree')
                branch = subprocess.run(['git', '-C', str(root), 'symbolic-ref', '--quiet', '--short', 'HEAD'], env=environment, capture_output=True, text=True, timeout=5)
                add('git', 'ok' if branch.returncode == 0 else 'note', 'Current branch: ' + branch.stdout.strip() if branch.returncode == 0 else 'Detached Git HEAD')
        except (OSError, subprocess.TimeoutExpired):
            add('git', 'warning', 'Git diagnostics could not complete within the read-only timeout')
    return {'active_feature': active.name if active else None, 'integration': state.get('integration') if state else None, 'acceptance': 'NOT_ASSESSED', 'errors': sum(item['severity'] == 'error' for item in findings), 'warnings': sum(item['severity'] == 'warning' for item in findings), 'notes': sum(item['severity'] == 'note' for item in findings), 'findings': findings}


def main():
    parser = argparse.ArgumentParser(description='Read-only Spec Kit project health check (current working directory).')
    parser.add_argument('--json', action='store_true', help='emit exactly one JSON object, without human output')
    arguments = parser.parse_args()
    try:
        result = diagnose(project_root())
    except (OSError, UnicodeError, ValueError) as exc:
        result = {'errors': 1, 'warnings': 0, 'notes': 0, 'findings': [{'section': 'diagnostic', 'severity': 'error', 'message': str(exc)}]}
    if arguments.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        section = None
        for finding in result['findings']:
            if section != finding['section']:
                section = finding['section']
                print('\n=== ' + section.title() + ' ===')
            print('  [' + finding['severity'].upper() + '] ' + finding['message'])
        print('\nSummary: {errors} error(s), {warnings} warning(s), {notes} note(s)'.format(**result))
    return 1 if result['errors'] else 0

if __name__ == '__main__':
    sys.exit(main())
