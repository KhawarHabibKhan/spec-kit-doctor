# Project Health Check — Spec Kit Extension

Read-only diagnostics for Spec Kit project structure, agent commands/skills, feature artifacts, scripts, extension configuration and Git context. Reports errors, warnings and notes; it does not repair files, install tools, change permissions, update an extension or run project scripts.

## Installation

The catalog and upstream v1.0.0 tag still contain the old implementation.
Install this maintained compatibility branch explicitly:

```bash
specify extension add doctor --from https://github.com/3pepe3/spec-kit-doctor/archive/refs/heads/fix/current-speckit-layout.zip
```

For reproducible installations, replace the branch archive with a reviewed
commit archive (`https://github.com/3pepe3/spec-kit-doctor/archive/<commit>.zip`).
Use `--force` only when intentionally replacing an installation after preserving
local customizations. Local development uses `specify extension add /path/to/checkout --dev`.

## Commands

Use `/speckit.doctor.check` (alias `/speckit.doctor`) in command-based integrations. In Codex's skills integration, use `$speckit-doctor-check` or its installed alias `$speckit-doctor`.

From the project root, run an installed script directly:

```bash
bash .specify/extensions/doctor/scripts/bash/doctor.sh
bash .specify/extensions/doctor/scripts/bash/doctor.sh --json
bash .specify/extensions/doctor/scripts/bash/doctor.sh --help
```

PowerShell entrypoint:

```powershell
& .specify/extensions/doctor/scripts/powershell/doctor.ps1
& .specify/extensions/doctor/scripts/powershell/doctor.ps1 -Json
& .specify/extensions/doctor/scripts/powershell/doctor.ps1 -Help
```

The nearest ancestor containing `.specify/` is inspected. `SPECIFY_INIT_DIR` explicitly selects a project root and fails if invalid. Both wrappers invoke the same `scripts/doctor.py` engine. Bash accepts `--json` and `--help`; PowerShell exposes `-Json` and `-Help`. Unknown arguments fail; there is no fix/apply mode. `PYTHON` may select a Python executable (one path, without arguments). Otherwise Bash uses `python3`; PowerShell looks for `python3`, then `python`.

JSON mode writes exactly one JSON object to stdout, including `active_feature`, `integration`, `acceptance: NOT_ASSESSED`, `errors`, `warnings`, `notes` and a `findings` array of `{section, severity, message}`. Counts exclude `ok` findings. Exit status is 0 with no errors (warnings/notes may remain), 1 with diagnostic errors, or 2 for invalid CLI arguments or missing Python in the Bash wrapper. Interpreter/startup failures are tooling failures and are not successful diagnostic reports. PowerShell may use its own nonzero parameter-binding error code for invalid flags.

## Checks and boundaries

- Current `.specify/scripts/`, `.specify/templates/`, `.specify/memory/constitution.md`; root-level legacy scripts/templates/memory remain supported only when no modern infrastructure directory exists and the complete legacy layout is present. A mixed layout is not silently treated as healthy.
- Optional `specs/` and numbered feature `spec.md`, `plan.md`, `tasks.md`. Missing specifications are errors; planning/task artifacts not yet generated are notes. File presence does not prove requirement quality or implementation acceptance.
- Native `.specify/integration.json` and `.specify/feature.json` are read when present. `SPECIFY_FEATURE_DIRECTORY` overrides the persisted feature pointer. Relative directory paths resolve from the project root; absolute paths are accepted. Active features must be numbered directories directly under `specs/`; symlinked, missing and outside paths fail. Shared `specs/contracts/` is not treated as a feature. Invalid JSON containers fail as diagnostics, not tracebacks.
- Current agent skill directories, including Codex `.agents/skills/speckit-*/SKILL.md`, and legacy command directories such as `.codex/prompts/`. Parent directories alone do not identify an integration. Unrelated `.agents/` content does not create a false Amp warning.
- The Bash and/or PowerShell script families actually present. A project may install only one family; the other family is not required. Present families are checked for four stable core scripts: `common`, `check-prerequisites`, `create-new-feature` and `setup-plan`. `setup-tasks`, `resolve-template` and `update-agent-context` are reported when present; a current layout is not marked broken because a version-specific helper is absent. The legacy layout retains its `update-agent-context` check. Bash execute permission is checked on non-Windows hosts.
- `.specify/extensions/.registry` JSON, with `registry.json` as a legacy fallback. A malformed current registry is not hidden by a valid legacy file. When both exist, the legacy file is explicitly reported as unvalidated. Validation covers the JSON container/entry shapes, not every installed extension's behavior or provenance.
- Optional `.specify/extensions.yml`: safe YAML parsing and top-level `hooks`/`installed` shapes when PyYAML is available. Without PyYAML, validation is explicitly unavailable and a warning is emitted; the tool never claims YAML is valid from file existence alone. It does not execute hooks or evaluate hook conditions.
- Git worktree/branch through read-only `rev-parse` and `symbolic-ref`, with optional locks disabled and bounded command timeouts. No index refresh, fetch, checkout or other mutation runs.

## Requirements and tests

Verified with Spec Kit1.2.2. Python 3.9+ and the platform wrapper shell are required. PyYAML is optional; install it into the interpreter selected by `PYTHON` to enable YAML validation. Spec Kit's own Python environment commonly includes it. Git is optional and its absence is a note.

Run fixture tests from this extension's checkout:

```bash
python3 -B -m unittest discover -s tests -v
bash -n scripts/bash/doctor.sh
```

Fixtures cover modern/legacy layouts, Codex skills, one script family, malformed registries/YAML, unavailable YAML validation, JSON escaping, argument handling and unchanged project bytes/modes/mtime. The YAML-parser fixture is skipped when PyYAML is absent. A PowerShell parity fixture runs when `pwsh` is installed; otherwise it is explicitly skipped. Both wrappers share diagnostic logic, but a skipped PowerShell fixture is not PowerShell runtime proof.

The extension manifest retains its existing MIT license declaration. This change does not invent an upstream license file or imply that diagnostics establish live integration, security or product acceptance.

Current layout references: [Spec Kit integrations](https://github.com/github/spec-kit/blob/main/docs/reference/integrations.md), [upgrade layout](https://github.com/github/spec-kit/blob/main/docs/upgrade.md).

Source/license metadata and its inherited limitation are recorded in [NOTICE.md](NOTICE.md).
