"""Validate the Phase 1 review snapshot, not runtime or legal compliance."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED_IDS = {
    "legacy-backend",
    "locateanything-code",
    "locateanything-model",
    "esp-idf",
    "esp-tinyusb",
    "esp32-camera",
    "vl53l5cx-reference",
    "lsm6dsox-driver",
    "android-usb-serial",
    "paddleseg",
    "paddleocr",
    "mediapipe",
    "pyserial",
    "fastapi",
    "uvicorn",
    "opencv-python-headless",
    "numpy",
}
DISPOSITIONS = {
    "adapt_candidate",
    "manifest_candidate",
    "reference_only",
    "blocked_use",
    "evaluation_only",
}
LICENSE_STATES = {"file_reviewed", "metadata_only", "conflicting_description"}
REPORTS = (
    "docs/dependencies/README.md",
    "docs/dependencies/REUSE_REVIEW.md",
    "docs/dependencies/ENVIRONMENT_GATES.md",
    "docs/hardware/INTERFACE_REVIEW.md",
    "docs/android-migration/PHASE1_RISKS.md",
    "exa-results/phase1-audit-2026-09-05/README.md",
)


def validate(data: object) -> list[str]:
    errors = []
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("phase") != 1:
        return ["invalid Phase 1 schema"]
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        return ["entries must be a nonempty list"]
    seen = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entry {index}: expected object")
            continue
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"entry {index}: invalid id")
            continue
        if identifier in seen:
            errors.append(f"{identifier}: duplicate id")
        seen.add(identifier)
        kind = entry.get("kind")
        if kind not in {"git", "model", "pypi"}:
            errors.append(f"{identifier}: invalid source kind")
        revision = entry.get("revision")
        if kind in {"git", "model"} and not re.fullmatch(r"[0-9a-f]{40}", str(revision)):
            errors.append(f"{identifier}: immutable revision required")
        if kind == "pypi" and not re.fullmatch(r"\d+(?:\.\d+)+", str(entry.get("version"))):
            errors.append(f"{identifier}: exact package version required")
        if entry.get("runtime_verified") is not False or entry.get("imported") is not False:
            errors.append(f"{identifier}: review snapshot must not claim runtime/import completion")
        gates = entry.get("gates")
        if (
            not isinstance(gates, list)
            or not gates
            or not all(isinstance(g, str) and g for g in gates)
        ):
            errors.append(f"{identifier}: explicit remaining gates required")
        if entry.get("disposition") not in DISPOSITIONS:
            errors.append(f"{identifier}: invalid disposition")
        license_info = entry.get("license")
        if not isinstance(license_info, dict):
            errors.append(f"{identifier}: license evidence required")
            continue
        if license_info.get("status") not in LICENSE_STATES or not license_info.get("label"):
            errors.append(f"{identifier}: invalid license review status")
        for field in (entry.get("repository"), license_info.get("url")):
            try:
                parsed = urlsplit(str(field))
                valid = parsed.scheme == "https" and parsed.hostname in {
                    "github.com",
                    "huggingface.co",
                    "pypi.org",
                }
            except ValueError:
                valid = False
            if not valid:
                errors.append(f"{identifier}: official HTTPS source URL required")
        if kind in {"git", "model"} and str(revision) not in str(license_info.get("url")):
            errors.append(f"{identifier}: license evidence must use the pinned revision")
        authorization = entry.get("usage_authorization")
        evaluation_authorized = (
            identifier == "locateanything-model"
            and isinstance(authorization, dict)
            and authorization.get("source") == "user"
            and authorization.get("scope") == "noncommercial_testing"
            and authorization.get("production_or_commercial_use") is False
            and authorization.get("license_basis") == license_info.get("url")
            and bool(authorization.get("statement"))
            and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(authorization.get("confirmed_on"))))
        )
        disposition = entry.get("disposition")
        if disposition == "evaluation_only" and not evaluation_authorized:
            errors.append(f"{identifier}: explicit limited evaluation authorization required")
        if license_info.get("status") == "conflicting_description":
            if disposition != "blocked_use" and not (
                disposition == "evaluation_only" and evaluation_authorized
            ):
                errors.append(f"{identifier}: conflicting license description cannot be released")
        if identifier == "locateanything-model":
            if disposition not in {"blocked_use", "evaluation_only"}:
                errors.append("locateanything-model: unrestricted use is not authorized")
            if not isinstance(gates, list) or "audit_remote_code" not in gates:
                errors.append("locateanything-model: remote code review gate must remain")
            if disposition == "blocked_use" and (
                not isinstance(gates, list) or "confirm_project_purpose" not in gates
            ):
                errors.append("locateanything-model: purpose confirmation gate must remain")
    if seen != REQUIRED_IDS:
        errors.append("source set differs from the reviewed 17-item scope")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        data = json.loads(
            (root / "docs/dependencies/sources.audit.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        print("FAIL: audit snapshot missing, unreadable, or invalid JSON")
        return 1
    errors = validate(data)
    for relative in REPORTS:
        path = root / relative
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"missing or empty report: {relative}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print("PASS: 17 pinned review sources, 6 reports, explicit runtime and license gates")
    print("Not an installation lock, vulnerability scan, legal clearance, or hardware test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
