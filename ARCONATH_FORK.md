# Arconath maintained fork

This repository is a narrow maintained fork of `NousResearch/hermes-agent`.
The `upstream` remote is fetch-only; production changes live on explicit
`arconath/*` branches and are never committed to the inspection clone.

## Patch inventory

1. Durable `/v1/runs` idempotency keyed by `Idempotency-Key` and
   `operation_id`, including conflict detection and operation lookup.
2. Durable, bounded, monotonic SSE event ids with `Last-Event-ID` replay and
   explicit replay-gap failure.
3. Current/next API bearer-key overlap for coordinated rotation.

These changes are API-server edge behavior. They do not add model tools or
alter prompt construction, provider routing, session history, or terminal
execution.

## Lifecycle

- Owner: Arconath platform runtime team.
- Runtime compatibility target: `NousResearch/hermes-agent` release `v0.20.6`,
  commit `5fc308a70719a83cccdbba4c0e39c23f5a8239d5`.
- Current development branch `arconath/agentdeck-contracts-v1` applies the
  AgentDeck patch commit `b1d574e2215c5dc48109f57e2768b1c57d97968a`
  on upstream-derived commit `ff3835a630deb1f03054806d91ae5712b76f16d1`.
  It is not a release artifact for `v0.20.6`.
- Local branch `arconath/agentdeck-contracts-v1-v0.20.6` is the exact-base
  backport candidate at `7ac3707bbf8a069aaae5acce387bc43e2ef5636b`, whose
  parent is the approved `5fc308a70719a83cccdbba4c0e39c23f5a8239d5`.
  Its stable patch id matches `b1d574e…`; workflow-authority validation and the
  focused 29-test AgentDeck run-contract suite pass. It remains local,
  unreviewed as a release, unpublished, and unsigned. Production still requires
  the full compatibility packet plus signed publication through release-control.
- Sync cadence: weekly and immediately for upstream security advisories.
- Security SLA: critical 24 hours, high 72 hours, other supported fixes 14 days.
- Compatibility gate: focused upstream API-server tests plus AgentDeck's
  pinned capability, idempotency, operation-lookup, SSE replay, approval,
  steer, stop, and artifact contracts.
- Publication authority: this repository emits a validation-only unsigned
  intent pinned to `registry.arconath.internal/arconath/hermes-agent`. Only the
  public, protected `Arconath/release-control` workflow may publish and sign
  the image through the canonical Distribution registry.
- Rollback: keep the prior release-control-signed image digest in platform
  GitOps; promotion changes only an immutable digest and never rewrites state.

Files under `.github/upstream-workflows/` preserve upstream CI definitions for
sync review but are intentionally inactive. Active workflows use only the
private `arconath-jit` runner group and reject public-fork pull requests before
a private runner can be scheduled.
