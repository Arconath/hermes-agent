"""Behavioral contracts for the Arconath Hermes workflow verifier."""

from __future__ import annotations

from dataclasses import replace
import importlib.util
from pathlib import Path
import sys

import pytest


_REPO = Path(__file__).resolve().parents[2]
_VERIFIER_PATH = _REPO / "scripts" / "verify-arconath-workflows.py"
_SPEC = importlib.util.spec_from_file_location("verify_arconath_workflows", _VERIFIER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_VERIFIER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _VERIFIER
_SPEC.loader.exec_module(_VERIFIER)

_UPSTREAM_PROVENANCE = _VERIFIER.ReleaseProvenance(
    source_repository="NousResearch/hermes-agent",
    source_revision="5fc308a70719a83cccdbba4c0e39c23f5a8239d5",
    source_ref="refs/tags/v2026.8.27",
    release_tag="v2026.8.27",
    release_version="0.20.6",
    release_date="2026.8.27",
)


_CONTRACTS_WORKFLOW = """\
name: contracts
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  contracts:
    if: >-
      github.repository == 'Arconath/hermes-agent' &&
      github.ref == 'refs/heads/main' &&
      github.ref_type == 'branch' &&
      github.ref_protected == true &&
      (github.event_name == 'push' || github.event_name == 'workflow_dispatch')
    runs-on:
      group: arconath-jit
      labels: [self-hosted, linux, x64, arconath-jit, rootless-buildkit]
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          persist-credentials: false
      - name: Verify
        shell: bash
        run: |
          set -Eeuo pipefail
          [[ \"$GITHUB_REF_PROTECTED\" == true ]]
"""

_DORMANT_RELEASE_WORKFLOW = """\
name: release intent (dormant)
on:
  # The upstream tag is validation provenance, not a fork release.
  workflow_dispatch:
permissions:
  contents: read
jobs:
  validate-intent:
    if: >-
      github.event_name == 'push' &&
      github.repository == 'Arconath/hermes-agent' &&
      github.ref == 'refs/tags/v2026.8.27' &&
      github.ref_type == 'tag' &&
      github.ref_protected == true
    runs-on:
      group: arconath-jit
      labels: [self-hosted, linux, x64, arconath-jit, rootless-buildkit]
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          fetch-depth: 0
          persist-credentials: false
      - name: Verify immutable intent and runner boundary
        shell: bash
        run: |
          set -Eeuo pipefail
          [[ "$GITHUB_REPOSITORY" == Arconath/hermes-agent ]]
          [[ "$GITHUB_REF_TYPE" == tag ]]
          case "$GITHUB_REF" in
            refs/tags/v2026.8.27) ;;
            *) echo 'untrusted upstream validation tag' >&2; exit 1 ;;
          esac
          [[ "$GITHUB_REF_PROTECTED" == true ]]
          [[ "$(git rev-parse 'refs/tags/v2026.8.27^{commit}')" == "$GITHUB_SHA" ]]
          [[ "$(git rev-parse 'refs/tags/v2026.8.27^{commit}')" == "5fc308a70719a83cccdbba4c0e39c23f5a8239d5" ]]
          [[ "$(git rev-parse HEAD)" == "$GITHUB_SHA" ]]
          [[ -f .github/workflows/arconath-release.yml ]]
          [[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]]
          [[ -z "${DOCKER_HOST:-}" ]]
          [[ -z "${CONTAINER_HOST:-}" ]]
          [[ ! -S /var/run/docker.sock ]]
          [[ ! -S "/run/user/$(id -u)/docker.sock" ]]
          [[ "${BUILDKIT_HOST:-}" =~ ^unix:///var/lib/arconath-runner/jobs/job\.[[:alnum:]]+/buildkit/buildkitd\.sock$ ]]
      - name: Verify contracts
        run: |
          set -Eeuo pipefail
          uv sync --locked --extra dev --extra messaging
          uv run --locked --extra dev --extra messaging ruff check gateway/platforms/api_server.py tests/gateway/test_api_server_runs.py
          uv run --locked --extra dev --extra messaging pytest -q tests/gateway/test_api_server_runs.py
      - name: Build non-publishable OCI validation candidate
        shell: bash
        run: |
          set -Eeuo pipefail
          archive="$RUNNER_TEMP/hermes-agent.oci.tar"
          release_version="$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
          release_date="$(python3 -c 'import re; from pathlib import Path; print(next(re.finditer(r"__release_date__\s*=\s*\"([^\"]+)\"", Path("hermes_cli/__init__.py").read_text(encoding="utf-8"))).group(1))')"
          [[ "$release_version" == "0.20.6" ]]
          [[ "$release_date" == "2026.8.27" ]]
          buildctl --addr "$BUILDKIT_HOST" build \
            --frontend dockerfile.v0 \
            --local context=. \
            --local dockerfile=. \
            --opt filename=Dockerfile \
            --opt platform=linux/amd64 \
            --output "type=oci,dest=$archive" \
            --attest type=sbom \
            --attest type=provenance,mode=max
          archive_sha="$(sha256sum "$archive" | awk '{print $1}')"
          jq -n \
            --arg repository "$GITHUB_REPOSITORY" \
            --arg sourceRevision "$GITHUB_SHA" \
            --arg sourceRef "$GITHUB_REF" \
            --arg releaseTag "$GITHUB_REF_NAME" \
            --arg releaseVersion "$release_version" \
            --arg releaseDate "$release_date" \
            --arg archiveSha256 "sha256:$archive_sha" \
            '{schemaVersion:1,artifactClass:"UnsignedHermesAgentReleaseIntent",deploymentAllowed:false,signatureState:"unsigned",repository:$repository,releaseTag:$releaseTag,releaseVersion:$releaseVersion,releaseDate:$releaseDate,sourceRevision:$sourceRevision,sourceRef:$sourceRef,archiveSha256:$archiveSha256,publisher:"Arconath/release-control",registryHost:"registry.arconath.internal",artifactRepository:"registry.arconath.internal/arconath/hermes-agent"}' \
            >"$RUNNER_TEMP/hermes-agent-release-intent.json"
          rm -- "$archive"
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: unsigned-hermes-agent-release-intent-${{ github.sha }}
          path: ${{ runner.temp }}/hermes-agent-release-intent.json
          if-no-files-found: error
          retention-days: 14
"""

_LEGACY_RELEASE_WORKFLOW = _DORMANT_RELEASE_WORKFLOW.replace(
    "  workflow_dispatch:",
    "  push:\n    tags:\n      - v2.337.0-arconath.1-rc.1",
).replace(
    "name: release intent (dormant)",
    "name: release intent",
)

_AUTOMATIC_RELEASE_WORKFLOW = _DORMANT_RELEASE_WORKFLOW.replace(
    "  workflow_dispatch:",
    "  push:\n    tags:\n      - v2026.8.27",
)


def _write_fixture(root: Path, release_workflow: str = _DORMANT_RELEASE_WORKFLOW) -> Path:
    workflow_root = root / ".github" / "workflows"
    workflow_root.mkdir(parents=True)
    (workflow_root / "arconath-contracts.yml").write_text(
        _CONTRACTS_WORKFLOW, encoding="utf-8"
    )
    (workflow_root / "arconath-release.yml").write_text(
        release_workflow, encoding="utf-8"
    )
    return workflow_root


def test_verifier_accepts_dormant_release_fixture(tmp_path):
    _VERIFIER.verify_workflows(_write_fixture(tmp_path))


def test_legacy_actions_runner_identity_is_rejected(tmp_path):
    with pytest.raises(_VERIFIER.WorkflowContractError, match="Actions Runner"):
        _VERIFIER.verify_workflows(_write_fixture(tmp_path, _LEGACY_RELEASE_WORKFLOW))


def test_automatic_release_trigger_is_rejected(tmp_path):
    with pytest.raises(_VERIFIER.WorkflowContractError, match="release trigger"):
        _VERIFIER.verify_workflows(_write_fixture(tmp_path, _AUTOMATIC_RELEASE_WORKFLOW))


def test_upstream_release_provenance_is_validation_only():
    assert (
        _VERIFIER.verify_release_provenance(_UPSTREAM_PROVENANCE)
        == "upstream-validation-only"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_revision", "7ac3707bbf8a069aaae5acce387bc43e2ef5636b"),
        ("source_ref", "refs/tags/v2026.8.28"),
        ("release_tag", "v2026.8.28"),
    ],
)
def test_release_provenance_rejects_tag_source_mismatch(field, value):
    mismatched = replace(_UPSTREAM_PROVENANCE, **{field: value})
    with pytest.raises(_VERIFIER.WorkflowContractError, match="does not match"):
        _VERIFIER.verify_release_provenance(mismatched)


def test_fork_cannot_reuse_upstream_release_identity():
    fork_claim = replace(
        _UPSTREAM_PROVENANCE,
        source_repository="Arconath/hermes-agent",
    )

    with pytest.raises(_VERIFIER.WorkflowContractError, match="not configured"):
        _VERIFIER.verify_release_provenance(fork_claim)
