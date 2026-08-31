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
