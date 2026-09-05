"""Static Phase 6 checks. This intentionally does not claim an Android build."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android"
REQUIRED = (
    "settings.gradle.kts",
    "build.gradle.kts",
    "gradle.properties",
    "app/build.gradle.kts",
    "app/proguard-rules.pro",
    "app/src/main/AndroidManifest.xml",
    "app/src/main/res/values/strings.xml",
    "app/src/main/res/values/themes.xml",
    "app/src/main/java/com/trollhunter/xglasses/MainActivity.kt",
    "app/src/main/java/com/trollhunter/xglasses/domain/AppState.kt",
    "app/src/main/java/com/trollhunter/xglasses/domain/AppReducer.kt",
    "app/src/main/java/com/trollhunter/xglasses/protocol/XgProtocol.kt",
    "app/src/main/java/com/trollhunter/xglasses/runtime/ModelRuntimeRegistry.kt",
    "app/src/main/java/com/trollhunter/xglasses/ui/XGlassesApp.kt",
    "app/src/main/java/com/trollhunter/xglasses/usb/UsbSessionManager.kt",
    "app/src/test/java/com/trollhunter/xglasses/domain/AppReducerTest.kt",
    "app/src/test/java/com/trollhunter/xglasses/protocol/XgProtocolTest.kt",
)


def check(root: Path = ANDROID) -> list[str]:
    errors = []
    missing = [relative for relative in REQUIRED if not (root / relative).is_file()]
    if missing:
        errors.extend(f"missing Android file: {relative}" for relative in missing)
        return errors
    manifest = (root / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
    if "android.hardware.usb.host" not in manifest:
        errors.append("USB Host feature missing")
    for permission in ("INTERNET", "CAMERA", "RECORD_AUDIO"):
        if f"android.permission.{permission}" in manifest:
            errors.append(f"unexpected permission: {permission}")
    state = (root / "app/src/main/java/com/trollhunter/xglasses/domain/AppState.kt").read_text(
        encoding="utf-8"
    )
    for task in ("NAVIGATION", "LOCATE_GRASP", "READ_TEXT", "SIGNAL", "DIALOGUE"):
        if task not in state:
            errors.append(f"missing task: {task}")
    if (
        "RuntimeState.NOT_INSTALLED" not in state
        or "safetyMonitoringActive" not in state
        or "TRANSPORT_OPEN" not in state
    ):
        errors.append("safe default runtime/monitoring state missing")
    sources = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.kt"))
    for forbidden in ("可以过街", "盲道", "斑马线", "http://", "https://"):
        if forbidden in sources:
            errors.append(f"forbidden Android source term: {forbidden}")
    usb = (root / "app/src/main/java/com/trollhunter/xglasses/usb/UsbSessionManager.kt").read_text(
        encoding="utf-8"
    )
    for required in (
        "UsbManager",
        "setPackage(context.packageName)",
        "FLAG_MUTABLE",
        "ACTION_USB_DEVICE_DETACHED",
        "4096",
    ):
        if required not in usb:
            errors.append(f"USB contract token missing: {required}")
    if re.search(r"vendorId\s*==|productId\s*==", usb):
        errors.append("USB device must be user-selected until VID/PID is frozen")
    protocol = (
        root / "app/src/main/java/com/trollhunter/xglasses/protocol/XgProtocol.kt"
    ).read_text(encoding="utf-8")
    for required in ("XG03", "XG_HEADER_SIZE = 36", "XG_MAX_PAYLOAD = 4096", "CRC32"):
        if required not in protocol:
            errors.append(f"protocol contract token missing: {required}")
    gradle = (root / "build.gradle.kts").read_text(encoding="utf-8")
    gradle += (root / "app/build.gradle.kts").read_text(encoding="utf-8")
    if re.search(r'version\s+"(?:latest|\+)|:[^"\n]*\+"', gradle, re.IGNORECASE):
        errors.append("floating Android dependency")
    return errors


def main() -> int:
    errors = check()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"PASS: {len(REQUIRED)} Android files and static safety contracts")
    print(
        "Not checked: Gradle resolution, compilation, APK, USB device, models, or phone performance."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
