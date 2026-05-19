---
name: NetBox Geo Delivery Orchestrator
description: Project-scoped Agency Agents skill and source of truth for auditing, planning, and delivering netbox-geo-foss.
upstream_repository: https://github.com/nullroute-commits/agency-agents
upstream_agents:
  - engineering/engineering-codebase-onboarding-engineer.md
  - engineering/engineering-software-architect.md
  - product/product-sprint-prioritizer.md
---

# NetBox Geo FOSS Agent Skill and Source of Truth

This file is the project-scoped source of truth for using the upstream
[agency-agents](https://github.com/nullroute-commits/agency-agents) collection
with this repository.

## Upstream source of truth

- Treat the upstream `agency-agents` repository as the canonical source for
  agent behavior and persona definitions.
- Prefer upstream updates over local rewrites when agent guidance changes.
- Use the upstream agent files listed in the frontmatter as the default role set
  for repository discovery, architecture decisions, and sprint planning.

## Local operating model

### 1. Repository discovery

Use **Codebase Onboarding Engineer** first for read-only exploration.

- Ground every explanation in inspected files.
- Confirm the active runtime and entry points before proposing work.
- Do not treat README claims as implemented features without code evidence.

### 2. Architecture decisions

Use **Software Architect** for structure, boundary, and consolidation work.

- Resolve conflicts between overlapping application layouts before adding new
  features.
- Record architectural trade-offs against the code that exists today.
- Treat `src/netbox_geo/` as the primary product package unless inspected code
  proves otherwise.

### 3. Delivery planning

Use **Sprint Prioritizer** for roadmap and sprint planning.

- Sequence work so build/test baselines are restored before feature expansion.
- Write acceptance criteria against executable behaviors, not documentation
  claims.
- Separate stabilization work from net-new feature work.

## Repository-specific facts to use as planning defaults

- Package metadata and CLI entrypoints live in `pyproject.toml` and
  `src/netbox_geo/`.
- Developer automation lives in `Makefile`.
- Container/runtime packaging lives in `Dockerfile` and the compose files.
- Tests must be treated carefully because the current suite mixes multiple
  application layouts.

## Validation defaults

Use the repository's existing validation commands before and after changes:

```bash
.venv/bin/pytest
.venv/bin/black --check src tests
.venv/bin/flake8 src tests
.venv/bin/isort --check-only src tests
.venv/bin/mypy src
```

## Expected outputs

When working in this repository:

1. Start with a factual inventory of the relevant files.
2. Call out delivery blockers and architectural drift explicitly.
3. Produce sprint plans with ordered milestones, dependencies, and acceptance
   criteria.
4. Keep this file aligned with the upstream agent set instead of inventing a
   separate local process.
