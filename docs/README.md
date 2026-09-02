# Hermes Agent fork documentation

Hermes is the upstream-derived personal AI agent core used across CLI, gateway,
TUI, desktop, tools, skills, plugins, and messaging platforms. This checkout is
an Arconath maintained fork; it is not a new portfolio product.

## Read by concern

| Concern | Document/area |
| --- | --- |
| Fork ownership and patches | [`../ARCONATH_FORK.md`](../ARCONATH_FORK.md) |
| Architecture decisions | [`ADR.md`](ADR.md) |
| Agent/runtime contract | [`AI-CONTEXT.md`](AI-CONTEXT.md) |
| Current maturity and blockers | [`STATUS.md`](STATUS.md) |
| Gateway/session/relay behavior | [`session-lifecycle.md`](session-lifecycle.md), [`relay-connector-contract.md`](relay-connector-contract.md), [`observability/README.md`](observability/README.md) |
| Desktop surface | [`../apps/desktop/README.md`](../apps/desktop/README.md), nested `AGENTS.md`, and `DESIGN.md` |
| Plugins/providers/skills | [`../plugins`](../plugins), [`../providers/README.md`](../providers/README.md), [`../skills`](../skills), and upstream website docs |
| Tests/evals | [`../tests`](../tests), [`../tests-js`](../tests-js), [`../evals`](../evals) |
| AgentDeck integration | [`Arconath/agentdeck/docs/hermes-integration.md`](https://github.com/Arconath/agentdeck/blob/main/docs/hermes-integration.md) |

## Reading rule

The root `AGENTS.md` is the governing intent layer. Read it before changing
core, gateway, desktop, plugin, provider, or contract code. Preserve the
upstream/fork distinction and update the patch inventory when behavior changes.

## Architecture diagram

- [Rendered architecture diagram](diagrams/architecture.svg)
- [Editable Mermaid source](diagrams/architecture.mmd)
