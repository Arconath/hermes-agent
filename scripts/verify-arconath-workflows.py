#!/usr/bin/env python3
"""Fail closed around Arconath fork workflow and release authority."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys


WORKFLOW_ROOT = Path(__file__).resolve().parents[1] / ".github" / "workflows"
RELEASE_WORKFLOW_NAME = "arconath-release.yml"
UPSTREAM_WORKFLOW_ROOT_NAME = "upstream-workflows"
EXPECTED_ACTIVE_WORKFLOWS = {"arconath-contracts.yml", RELEASE_WORKFLOW_NAME}
EXPECTED_RUNNER = (
    "runs-on:\n"
    "      group: arconath-jit\n"
    "      labels: [self-hosted, linux, x64, arconath-jit, rootless-buildkit]"
)

UPSTREAM_REPOSITORY = "NousResearch/hermes-agent"
UPSTREAM_RELEASE_TAG = "v2026.8.27"
UPSTREAM_RELEASE_COMMIT = "5fc308a70719a83cccdbba4c0e39c23f5a8239d5"
UPSTREAM_RELEASE_VERSION = "0.20.6"
UPSTREAM_RELEASE_DATE = "2026.8.27"
LEGACY_ACTIONS_RUNNER_TAG = re.compile(
    r"^v2\.337\.0(?:[-.][A-Za-z0-9.-]+)?$"
)


class WorkflowContractError(ValueError):
    """Raised when a workflow or provenance contract is unsafe."""


@dataclass(frozen=True)
class ReleaseProvenance:
    """Immutable release metadata supplied by a source checkout."""

    source_repository: str
    source_revision: str
    source_ref: str
    release_tag: str
    release_version: str
    release_date: str


UPSTREAM_VALIDATION_PROVENANCE = ReleaseProvenance(
    source_repository=UPSTREAM_REPOSITORY,
    source_revision=UPSTREAM_RELEASE_COMMIT,
    source_ref=f"refs/tags/{UPSTREAM_RELEASE_TAG}",
    release_tag=UPSTREAM_RELEASE_TAG,
    release_version=UPSTREAM_RELEASE_VERSION,
    release_date=UPSTREAM_RELEASE_DATE,
)


def verify_release_provenance(provenance: ReleaseProvenance) -> str:
    """Accept only the known upstream provenance as validation-only input.

    The returned state is deliberately not a release state. No Arconath fork
    release identity exists in source evidence, so an Arconath repository or a
    legacy Actions Runner-style tag must never be treated as this provenance.
    """

    if LEGACY_ACTIONS_RUNNER_TAG.fullmatch(provenance.release_tag):
        raise WorkflowContractError(
            "legacy Actions Runner v2.337.0 identity is not a Hermes release"
        )

    expected = UPSTREAM_VALIDATION_PROVENANCE
    if provenance.source_repository != expected.source_repository:
        raise WorkflowContractError(
            "fork release identity is not configured; only upstream provenance "
            "is accepted for validation"
        )

    fields = (
        ("source revision", provenance.source_revision, expected.source_revision),
        ("source ref", provenance.source_ref, expected.source_ref),
        ("release tag", provenance.release_tag, expected.release_tag),
        ("release version", provenance.release_version, expected.release_version),
        ("release date", provenance.release_date, expected.release_date),
    )
    for label, actual, expected_value in fields:
        if actual != expected_value:
            raise WorkflowContractError(
                f"upstream release {label} does not match its immutable source identity"
            )

    if provenance.source_ref != f"refs/tags/{provenance.release_tag}":
        raise WorkflowContractError("release tag and source ref do not match")

    return "upstream-validation-only"


def _fail(message: str) -> None:
    raise WorkflowContractError(message)


def _verify_common_workflow_contract(workflow: Path, workflow_text: str) -> None:
    forbidden = {
        "GitHub-hosted runner": r"runs-on\s*:\s*[^\n]*(?:ubuntu|macos|windows)",
        "package publication permission": r"packages\s*:\s*write",
        "OIDC signing permission": r"id-token\s*:\s*write",
        "Cosign signing": r"\bcosign\s+sign(?:-blob)?\b",
        "BuildKit registry push": r"(?:push\s*:\s*true|--output[^\n]*type=registry|--push\b)",
        "deployment command": r"\b(?:kubectl|helm|flux)\s+(?:apply|install|upgrade|reconcile)\b",
    }
    for authority, pattern in forbidden.items():
        if re.search(pattern, workflow_text, flags=re.IGNORECASE):
            _fail(f"{workflow.name} contains forbidden {authority}")

    if EXPECTED_RUNNER not in workflow_text:
        _fail(f"{workflow.name} must use the canonical private runner group and labels")
    if re.search(r"^\s*uses:", workflow_text, flags=re.MULTILINE) and (
        "persist-credentials: false" not in workflow_text
    ):
        _fail(f"{workflow.name} must not persist checkout credentials")
    for action in re.findall(
        r"^\s*uses:\s*([^\s#]+)", workflow_text, flags=re.MULTILINE
    ):
        if action.startswith("./"):
            continue
        if not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", action):
            _fail(f"{workflow.name} uses an action that is not pinned to a commit: {action}")
    if re.search(r"^\s*[A-Za-z0-9_-]+:\s*write\s*$", workflow_text, flags=re.MULTILINE):
        _fail(f"{workflow.name} must not request writable permissions")


def _verify_contracts_workflow(workflow_text: str) -> None:
    required = (
        "branches: [main]",
        "github.repository == 'Arconath/hermes-agent'",
        "github.ref == 'refs/heads/main'",
        "github.ref_type == 'branch'",
        "github.ref_protected == true",
        "github.event_name == 'push' || github.event_name == 'workflow_dispatch'",
        '[[ "$GITHUB_REF_PROTECTED" == true ]]',
    )
    for contract in required:
        if contract not in workflow_text:
            _fail(f"arconath-contracts.yml is missing protected-ref contract: {contract}")
    if re.search(r"^\s*pull_request\s*:", workflow_text, flags=re.MULTILINE):
        _fail("arconath-contracts.yml must not schedule pull-request source on private runner")
    if re.search(r"source_commit|github\.event\.pull_request", workflow_text):
        _fail("arconath-contracts.yml contains arbitrary source selection")


def _verify_dormant_release_workflow(workflow_text: str) -> None:
    """Require the release file to remain inert until fork governance exists.

    The validation candidate is intentionally retained as an inspection aid,
    but its only event is manual dispatch and its job requires a push event.
    Consequently it cannot allocate a runner or emit an artifact today. The
    exact upstream provenance checks stay here so a future governance change
    cannot silently turn a different tag into this validation identity.
    """

    if re.search(r"v2\.337\.0", workflow_text):
        _fail("arconath-release.yml contains the unrelated Actions Runner release identity")
    if re.search(
        r"^\s*(?:push|pull_request|workflow_call|repository_dispatch|release|schedule|workflow_run)\s*:",
        workflow_text,
        flags=re.MULTILINE,
    ):
        _fail("arconath-release.yml must remain without a release trigger")
    if not re.search(r"^\s*workflow_dispatch\s*:", workflow_text, flags=re.MULTILINE):
        _fail("arconath-release.yml must retain only its dormant inspection trigger")
    if re.search(r"^\s*inputs\s*:", workflow_text, flags=re.MULTILINE):
        _fail("arconath-release.yml must not accept arbitrary dispatch input")
    if re.search(r"^\s*tags\s*:", workflow_text, flags=re.MULTILINE):
        _fail("arconath-release.yml must not configure a release tag without fork evidence")
    if "github.event_name == 'push'" not in workflow_text:
        _fail("arconath-release.yml must keep its manual job unreachable")
    for contract in (
        "github.repository == 'Arconath/hermes-agent'",
        f"github.ref == 'refs/tags/{UPSTREAM_RELEASE_TAG}'",
        "github.ref_type == 'tag'",
        "github.ref_protected == true",
        f"refs/tags/{UPSTREAM_RELEASE_TAG})",
        f"refs/tags/{UPSTREAM_RELEASE_TAG}^{{commit}}",
        f'== "{UPSTREAM_RELEASE_COMMIT}"',
        'git rev-parse HEAD)" == "$GITHUB_SHA"',
        '[[ -f .github/workflows/arconath-release.yml ]]',
        'git status --porcelain=v1 --untracked-files=all',
        '"${DOCKER_HOST:-}"',
        '"${CONTAINER_HOST:-}"',
        "type=oci,dest=$archive",
        "--attest type=sbom",
        "--attest type=provenance,mode=max",
        f'[[ "$release_version" == "{UPSTREAM_RELEASE_VERSION}" ]]',
        f'[[ "$release_date" == "{UPSTREAM_RELEASE_DATE}" ]]',
        '--arg sourceRevision "$GITHUB_SHA"',
        '--arg sourceRef "$GITHUB_REF"',
        '--arg releaseTag "$GITHUB_REF_NAME"',
        '--arg releaseVersion "$release_version"',
        '--arg releaseDate "$release_date"',
        'artifactClass:"UnsignedHermesAgentReleaseIntent"',
        "deploymentAllowed:false",
        'signatureState:"unsigned"',
        'sourceRevision:$sourceRevision',
        'sourceRef:$sourceRef',
        'publisher:"Arconath/release-control"',
        'registryHost:"registry.arconath.internal"',
        'artifactRepository:"registry.arconath.internal/arconath/hermes-agent"',
        'rm -- "$archive"',
    ):
        if contract not in workflow_text:
            _fail(f"arconath-release.yml is missing dormant boundary contract: {contract}")
    if re.search(r"source_commit|github\.event\.pull_request", workflow_text):
        _fail("arconath-release.yml contains arbitrary source selection")


def verify_workflows(workflow_root: Path = WORKFLOW_ROOT) -> None:
    """Verify workflow authority using the supplied workflow fixture root."""

    workflow_root = Path(workflow_root)
    active_workflows = sorted(workflow_root.glob("*.yml")) + sorted(
        workflow_root.glob("*.yaml")
    )
    if not active_workflows:
        _fail("no active workflow was found")

    if {workflow.name for workflow in active_workflows} != EXPECTED_ACTIVE_WORKFLOWS:
        _fail("active workflow set drifted; upstream workflow copies must remain inactive")

    upstream_workflow_root = workflow_root.parent / UPSTREAM_WORKFLOW_ROOT_NAME
    if upstream_workflow_root.exists():
        if not upstream_workflow_root.is_dir():
            _fail("upstream workflow archive path is not a directory")
        if {path.name for path in upstream_workflow_root.iterdir()} & EXPECTED_ACTIVE_WORKFLOWS:
            _fail("an upstream workflow has crossed into the active workflow namespace")

    for workflow in active_workflows:
        workflow_text = workflow.read_text(encoding="utf-8")
        _verify_common_workflow_contract(workflow, workflow_text)

        if workflow.name == "arconath-contracts.yml":
            _verify_contracts_workflow(workflow_text)
        elif workflow.name == RELEASE_WORKFLOW_NAME:
            _verify_dormant_release_workflow(workflow_text)


def main() -> int:
    try:
        verify_workflows()
    except WorkflowContractError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        "Arconath workflow authority is validation-only; no protected fork "
        "release identity is configured"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
