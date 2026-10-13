# Spec Kit Doctor

A Spec Kit extension that diagnoses project health and reports issues.

## What it does

Scans your Spec Kit project and checks 6 areas:

- **Project structure** — are `.specify/`, `specs/`, `.specify/scripts/`, `.specify/templates/`, `.specify/memory/` present?
- **AI agent configuration** — which agent is set up, do its commands exist?
- **Feature specifications** — for each feature, are spec.md/plan.md/tasks.md present?
- **Scripts health** — are all bash and PowerShell scripts present and executable?
- **Extensions health** — is extensions.yml valid, is the registry intact?
- **Git status** — are you in a repo, what branch?

Reports findings as errors, warnings, and notes with suggested fixes.

## Installation

```bash
specify extension add doctor
```

Or install from GitHub:

```bash
specify extension add doctor --from https://github.com/KhawarHabibKhan/spec-kit-doctor/archive/refs/tags/v1.0.0.zip
```

## Usage

```
/speckit.doctor.check
```

Or using the alias:

```
/speckit.doctor
```

## Requirements

- Spec Kit >= 0.1.0

## Bash compatibility checks

The Bash diagnostic supports the current `.specify/` layout, Codex skills in
`.agents/skills/`, and the `.specify/extensions/.registry` registration file.
It no longer requires the retired update-agent-context script. `--json` writes
only JSON to stdout, with human diagnostics on stderr. Run the regression test
with `python3 -m unittest discover -s tests -v`. These changes and tests cover
Bash; the PowerShell probe has not yet been brought to parity.
