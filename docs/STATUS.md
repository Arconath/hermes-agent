# Hermes Agent fork status and blockers

**Reviewed:** 2026-09-02

## Lifecycle

Maintained Arconath fork of the upstream Hermes Agent. It is a platform/runtime
dependency for AgentDeck and related infrastructure, not a separate public
Arconath portfolio product.

## Evidence register

| Area | State | Evidence | Meaning |
| --- | --- | --- | --- |
| Upstream/fork identity | PASS (local exact-base candidate), release review required | [`../ARCONATH_FORK.md`](../ARCONATH_FORK.md) | Runtime target is upstream `v0.20.6`/`5fc308a…`; local backport `7ac3707…` has that exact parent and a stable patch id identical to the newer development patch, but is not pushed, signed, or released |
| Maintained patches and readiness validation | IMPLEMENTED FOUNDATION | `ARCONATH_FORK.md`, gateway source/tests | Idempotency, SSE replay, and key overlap remain bounded edge behavior; `c439160…` makes the healthy readiness fixture independent of host disk pressure without changing the production probe or safety checks; the focused gateway suite passes 29 tests on the current development branch |
| CLI/gateway/TUI/desktop/plugin breadth | IMPLEMENTED UPSTREAM FOUNDATION | source tree, docs, tests/evals | Each surface has its own verification and compatibility boundaries |
| AgentDeck runtime compatibility | CONTRACTED | AgentDeck integration docs and fork contract | Exact runtime/client release smoke remains required |
| Upstream security/sync lifecycle | OPEN | fork contract | Weekly/security sync and SLA need ongoing owner evidence |
| Protected artifact publication | BLOCKED until configured | fork contract and root readiness | Release-control/registry/signing/rollback evidence remains external |

## Open blockers

- current upstream sync/security review and compatibility test packet;
- independent review and the full compatibility packet for local exact-base
  backport `7ac3707…` before any production image is built;
- exact runtime-facing AgentDeck idempotency/SSE/approval/steer/stop/artifact
  acceptance for the release under consideration;
- protected release-control publication, signed digest, SBOM/provenance,
  vulnerability and rollback evidence;
- live runtime/desktop/device/network acceptance where claimed.

## Next milestone

Close the fork/runtime compatibility packet against the pinned upstream base,
then publish only through the protected release-control path and validate the
exact digest with Hermes Runtime and AgentDeck.
