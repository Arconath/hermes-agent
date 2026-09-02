# AI context: Arconath Hermes Agent fork

**Reviewed:** 2026-08-31

## Identity and fork boundary

Hermes is a personal AI agent with one agent core shared by CLI, messaging
gateway, TUI, desktop, tools, skills, schedulers, and plugins. Arconath keeps a
narrow maintained fork of `NousResearch/hermes-agent`; `ARCONATH_FORK.md` is the
source of truth for patch inventory, upstream base, owner, sync cadence, SLA,
compatibility tests, and publication/rollback policy.

The current Arconath patches are API-server edge behavior: durable `/v1/runs`
idempotency, bounded SSE event IDs/replay, and current/next bearer-key overlap.
They must not alter prompt construction, provider routing, session history, or
terminal execution unless a separately reviewed patch says so.

## Component map

| Area | Responsibility |
| --- | --- |
| `run_agent.py`, `agent/` | Core agent loop, context, tools, providers, memory |
| `gateway/` | Messaging/web/API gateway, session routing, cron, relay, auth |
| `tui_gateway/`, `ui-tui/` | TUI transport and interface |
| `apps/desktop/` | Electron/native desktop surface; read its nested guide |
| `plugins/`, `optional-skills/`, `skills/` | Extension/skill surfaces with separate discovery contracts |
| `providers/`, `plugins/model-providers/` | Provider registry and adapters |
| `tests/`, `tests-js/`, `evals/` | Python/JS regression tests and research/eval evidence |

## Invariants

- Per-conversation prompt caching is sacred: do not mutate the cached prefix,
  swap toolsets, or rebuild the system prompt mid-conversation except for the
  explicitly designed compression path.
- Keep the core as a narrow waist; add capability at the edge via existing
  code, CLI+skill, service-gated tool, plugin, or MCP before a new core tool.
- Preserve strict message-role alternation, session/profile identity, and
  authority-aware state routing.
- Non-secret behavior belongs in `config.yaml`; `.env` is for credentials,
  tokens, and passwords.
- Plugin discovery, provider discovery, memory-provider discovery, and desktop
  plugin surfaces are distinct; do not conflate them or hardcode plugin logic
  into core files.
- User/provider/dependency updates remain pinned according to the repository
  policy; retain compatibility tests and real-path E2E checks.
- Outbound telemetry and third-party integrations require explicit opt-in and
  should not be copied into core as product-specific code.

## Fork maintenance workflow

1. Read root and nested `AGENTS.md` plus the relevant subsystem README.
2. Reproduce behavior against the current fork and inspect upstream intent/history.
3. Keep the change in the narrowest surface; update `ARCONATH_FORK.md` if the
   patch inventory/contract changes.
4. Run focused real-path tests, then the relevant Python/JS/desktop/eval suites.
5. Rebase/sync from the fetch-only upstream remote on the documented cadence,
   re-run AgentDeck compatibility fixtures for runtime-facing changes, and
   retain rollback identity before publication.

## Stop conditions

Do not add a new core tool when an edge/plugin/skill suffices, change cache or
profile identity casually, add non-secret user settings to `.env`, expose
credentials, execute untrusted fork code on the private runner, or publish the
fork without release-control evidence and platform-owner approval.
