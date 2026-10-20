---
description: "Run a read-only project health diagnostic for structure, agent commands/skills, feature artifacts, scripts, extensions and Git context."
scripts:
  sh: scripts/bash/doctor.sh
  ps: scripts/powershell/doctor.ps1
---

# Project Health Check

Inspect the current Spec Kit project without changing it. This command reports diagnostic findings; it does not authorize or execute repairs, installs, upgrades, hook commands or permission changes.

## User Input

```text
$ARGUMENTS
```

Consider the input as diagnostic options, not executable shell text. Supported options are `--json`/`--help` for Bash and `-Json`/`-Help` for PowerShell. Reject other options. There is no fix mode.

## Outline

1. Execute `{SCRIPT}` from the project root with only supported diagnostic flags. Use the installed script; do not generate a separate project-specific scanner. If Python cannot start, report a tooling failure rather than healthy results.
2. Review six areas: current `.specify/` infrastructure (or the explicit legacy layout), actual agent command/skill directories, feature artifacts, the installed script families, extension configuration/registry, and read-only Git context. Codex skills use `.agents/skills/`; an unrelated `.agents/` directory is not proof of Amp. Current extension metadata uses `.specify/extensions/.registry`, with an explicit legacy `registry.json` fallback.
3. Report errors, warnings, notes and validation limits. JSON mode emits one object only, without a human prefix. Missing PyYAML means YAML was not validated. File presence, clean diagnostics and command discovery do not prove working runtime integration or feature acceptance.
4. Explain the smallest relevant correction as a suggestion. Do not automatically run `specify init`, force an overwrite, update/remove an extension, copy a constitution, edit a plan, change permissions, or commit anything. Existing project rules and owner authorization govern any separate corrective task. Preserve customizations before any approved upgrade.
