"""Read-only foundation and current runtime-scope checks; not hardware certification."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

CONSTRUCTION = (
    "CODEX_START_HERE CODEX_MASTER_REQUIREMENTS ARCHITECTURE CONSTRUCTION_PLAN "
    "DEV_PROGRESS LOG HANDOFF WORKFLOW GITHUB_ROLLBACK TEST_METRICS LAYER_CONTRACT TOOL_POLICY"
).split()
LAYERS = (
    "00-foundation 01-deps-license 02-glasses-link 03-core-navigation "
    "04-locate-grasp 05-assist-functions 06-android-migration"
).split()
DIRECTORIES = (
    "firmware server server/input server/common server/api server/perception/navigation "
    "server/perception/locate server/perception/assist server/arbitration server/output "
    "frontend tools tests docs/android-migration"
).split()
REQUIRED = (
    ["AGENTS.md", "README.md", "方案V3.md", "X-Glasses施工规范V3.md", "MEMORY.md"]
    + [".gitignore", ".gitattributes", ".env.example", "requirements-dev.txt", "pyproject.toml"]
    + [
        "docs/product/PRODUCT_REQUIREMENTS.md",
        "tools/check_foundation.py",
        "tests/test_foundation.py",
    ]
    + [f"docs/construction/{name}.md" for name in CONSTRUCTION]
    + [f"docs/construction/progress/layers/{name}.md" for name in LAYERS]
    + [f"{name}/README.md" for name in DIRECTORIES]
)
IGNORED = (
    ".venv/probe .env .env.local config.local.json secrets/probe.key "
    "models/probe weights/probe datasets/probe recordings/probe "
    "logs/probe.log node_modules/probe frontend/dist/probe firmware/build/probe "
    "firmware/.pio/probe __pycache__/probe.pyc"
).split()

RUNTIME_FILES = {
    "firmware/CMakeLists.txt",
    "firmware/sdkconfig.defaults",
    "firmware/main/CMakeLists.txt",
    "firmware/main/idf_component.yml",
    "firmware/main/main.c",
    "firmware/main/xg_protocol.h",
    "firmware/main/xg_protocol.c",
    "firmware/main/xg_controller.h",
    "firmware/main/xg_controller.c",
    "server/common/clock.py",
    "server/common/control.py",
    "server/common/protocol.py",
    "server/common/sensors.py",
    "server/input/frames.py",
    "server/input/link.py",
    "server/input/serial_port.py",
    "server/input/stream.py",
    "server/input/recording.py",
    "server/api/__init__.py",
    "server/api/__main__.py",
    "server/api/http.py",
    "server/api/state.py",
    "frontend/index.html",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/tsconfig.json",
    "frontend/vite.config.ts",
    "frontend/src/App.tsx",
    "frontend/src/api.ts",
    "frontend/src/main.tsx",
    "frontend/src/styles.css",
    "frontend/src/types.ts",
    "frontend/src/vite-env.d.ts",
    "frontend/src/test/setup.ts",
    "frontend/src/App.test.tsx",
    "server/perception/navigation/contracts.py",
    "server/perception/navigation/fusion.py",
    "server/perception/navigation/worker.py",
}
REQUIRED += sorted(RUNTIME_FILES) + [
    "docs/protocol/USB_V1.md",
    "tools/replay_usb.py",
    "tests/test_usb_protocol.py",
    "tests/test_usb_recording.py",
    "tests/test_usb_control.py",
    "docs/protocol/CONTROL_V1.md",
    "requirements-input.txt",
    "tools/usb_probe.py",
    "tests/test_serial_port.py",
    "docs/dependencies/INPUT_RUNTIME.md",
    "docs/construction/VSCODE.md",
    "tools/check_firmware_contract.py",
    "tests/test_firmware_contract.py",
    "docs/protocol/LOCAL_API_V1.md",
    "tests/test_local_api.py",
    "docs/dependencies/FRONTEND_RUNTIME.md",
    "docs/protocol/NAVIGATION_CORE_V1.md",
    "tests/test_navigation_core.py",
    "docs/protocol/SEGMENTATION_WORKER_V1.md",
    "docs/dependencies/SEGMENTATION_RUNTIME.md",
    "tests/test_segmentation_worker.py",
]


def check_content(root: Path) -> list[str]:
    """Validate structure and empty configuration without network or model imports."""
    errors = []
    contents = {}
    for relative in REQUIRED:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing file: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            errors.append(f"unreadable file: {relative}: {type(exc).__name__}")
            continue
        contents[relative] = content
        if not content.strip():
            errors.append(f"empty file: {relative}")
        if re.search(r"^(?:<{7}|={7}|>{7})(?:\s|$)", content, re.MULTILINE):
            errors.append(f"conflict marker: {relative}")
        if relative.endswith(".md"):
            # Simple inline links only; do not fetch external URLs or validate anchors.
            for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", content):
                target = target.strip().removeprefix("<").removesuffix(">")
                parts = urlsplit(target)
                if parts.scheme or parts.netloc or not parts.path:
                    continue
                candidate = (path.parent / unquote(parts.path)).resolve()
                if not candidate.is_relative_to(root.resolve()) or not candidate.exists():
                    errors.append(f"broken or external local link: {relative}")

    for number, line in enumerate(contents.get(".env.example", "").splitlines(), 1):
        line = line.strip()
        if line and not line.startswith("#"):
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*=", line):
                # Never echo values, which may contain accidentally pasted secrets.
                errors.append(f"nonempty or malformed env placeholder: line {number}")
    if "requirements-dev.txt" in contents:
        entries = [
            line.strip()
            for line in contents["requirements-dev.txt"].splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if entries != ["ruff==0.12.12"]:
            errors.append("Phase 0 dependencies differ from reviewed Ruff-only pin")
    for directory in ("firmware", "server", "frontend"):
        for path in (root / directory).rglob("*"):
            if not path.is_file() or path.name == "README.md":
                continue
            if any(part in {"node_modules", "dist"} for part in path.parts):
                continue
            if "__pycache__" in path.parts and path.suffix == ".pyc":
                continue
            if path.relative_to(root).as_posix() not in RUNTIME_FILES:
                errors.append(
                    f"unexpected runtime file outside current scope: {path.relative_to(root)}"
                )
    return errors


def check_git(root: Path) -> list[str]:
    """Probe ignores without creating sensitive files."""
    errors = []
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )
        if result.returncode or Path(result.stdout.strip()).resolve() != root.resolve():
            return ["project root is not the Git worktree root"]
        for relative, expected in [(name, 0) for name in IGNORED] + [(".env.example", 1)]:
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", "--", relative],
                cwd=root,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if result.returncode != expected:
                errors.append(f"ignore rule mismatch or Git error: {relative}")
    except (OSError, subprocess.TimeoutExpired):
        errors.append("Git unavailable or timed out")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check_content(root) + check_git(root)
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print(f"PASS: {len(REQUIRED)} required files, current scope/config, and Git ignore probes")
    print("Not checked: semantic safety, external URLs, business functions, models, hardware.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
