#!/usr/bin/env python3
"""Fail closed when an active Arconath fork workflow gains release authority."""

from pathlib import Path
import re


WORKFLOW_ROOT = Path(__file__).resolve().parents[1] / ".github" / "workflows"
RELEASE_WORKFLOW = WORKFLOW_ROOT / "arconath-release.yml"


def fail(message: str) -> None:
    raise SystemExit(message)


active_workflows = sorted(WORKFLOW_ROOT.glob("*.yml")) + sorted(
    WORKFLOW_ROOT.glob("*.yaml")
)
if not active_workflows:
    fail("no active workflow was found")

for workflow in active_workflows:
    workflow_text = workflow.read_text(encoding="utf-8")
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
            fail(f"{workflow.name} contains forbidden {authority}")

    # These workflows run on the private arconath-jit fleet. A public fork
    # cannot use a broad branch/tag glob, pull-request source, or arbitrary
    # dispatch input as a trust boundary. The GitHub ref-protection bit is
    # intentionally required in both the expression and the shell preflight:
    # an unprotected ref must result in a skipped job, never a private-runner
    # allocation.
    if workflow.name == "arconath-contracts.yml":
        required = (
            "branches: [main]",
            "github.repository == 'Arconath/hermes-agent'",
            "github.ref == 'refs/heads/main'",
            "github.ref_type == 'branch'",
            "github.ref_protected == true",
            'github.event_name == \'push\' || github.event_name == \'workflow_dispatch\'',
            '[[ "$GITHUB_REF_PROTECTED" == true ]]',
        )
        for contract in required:
            if contract not in workflow_text:
                fail(f"arconath-contracts.yml is missing protected-ref contract: {contract}")
        if re.search(r"^\s*pull_request\s*:", workflow_text, flags=re.MULTILINE):
            fail("arconath-contracts.yml must not schedule pull-request source on private runner")
        if re.search(r"source_commit|github\.event\.pull_request", workflow_text):
            fail("arconath-contracts.yml contains arbitrary source selection")

    if workflow.name == "arconath-release.yml":
        required = (
            "tags: ['v2.337.0-arconath.*']",
            "github.repository == 'Arconath/hermes-agent'",
            "startsWith(github.ref, 'refs/tags/v2.337.0-arconath.')",
            "github.ref_type == 'tag'",
            "github.ref_protected == true",
            "github.event_name == 'push'",
            '[[ "$GITHUB_REF_PROTECTED" == true ]]',
        )
        for contract in required:
            if contract not in workflow_text:
                fail(f"arconath-release.yml is missing protected-tag contract: {contract}")
        if re.search(r"workflow_dispatch|pull_request|source_commit", workflow_text):
            fail("arconath-release.yml must not support arbitrary source dispatch")

release = RELEASE_WORKFLOW.read_text(encoding="utf-8")
required_contracts = (
    'artifactClass:"UnsignedHermesAgentReleaseIntent"',
    "deploymentAllowed:false",
    'signatureState:"unsigned"',
    'publisher:"Arconath/release-control"',
    'registryHost:"registry.arconath.internal"',
    'artifactRepository:"registry.arconath.internal/arconath/hermes-agent"',
    'rm -- "$archive"',
)
for contract in required_contracts:
    if contract not in release:
        fail(f"arconath-release.yml is missing required contract: {contract}")

print("Arconath workflow authority is validation-only and Distribution-pinned")
