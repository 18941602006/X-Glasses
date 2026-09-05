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
    "app/src/main/java/com/trollhunter/xglasses/protocol/ControlSession.kt",
    "app/src/main/java/com/trollhunter/xglasses/runtime/ModelRuntimeRegistry.kt",
    "app/src/main/java/com/trollhunter/xglasses/navigation/NavigationContracts.kt",
    "app/src/main/java/com/trollhunter/xglasses/navigation/NavigationEngine.kt",
    "app/src/main/java/com/trollhunter/xglasses/navigation/OpenNavigationProvider.kt",
    "app/src/main/java/com/trollhunter/xglasses/navigation/NavigationProviderFactory.kt",
    "app/src/main/java/com/trollhunter/xglasses/navigation/AndroidLocationSource.kt",
    "app/src/main/java/com/trollhunter/xglasses/navigation/NavigationCoordinator.kt",
    "app/src/main/java/com/trollhunter/xglasses/ui/XGlassesApp.kt",
    "app/src/main/java/com/trollhunter/xglasses/usb/UsbSessionManager.kt",
    "app/src/main/java/com/trollhunter/xglasses/usb/AndroidHostLink.kt",
    "app/src/test/java/com/trollhunter/xglasses/domain/AppReducerTest.kt",
    "app/src/test/java/com/trollhunter/xglasses/protocol/XgProtocolTest.kt",
    "app/src/test/java/com/trollhunter/xglasses/protocol/ControlSessionTest.kt",
    "app/src/test/java/com/trollhunter/xglasses/navigation/NavigationEngineTest.kt",
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
    for permission in ("INTERNET", "ACCESS_COARSE_LOCATION", "ACCESS_FINE_LOCATION"):
        if f"android.permission.{permission}" not in manifest:
            errors.append(f"required navigation permission missing: {permission}")
    for permission in ("CAMERA", "RECORD_AUDIO", "ACCESS_BACKGROUND_LOCATION"):
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
    if "RepeatLastOutput" not in state:
        errors.append("repeat action missing")
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
    control = (
        root / "app/src/main/java/com/trollhunter/xglasses/protocol/ControlSession.kt"
    ).read_text(encoding="utf-8")
    for required in (
        "HANDSHAKE_TIMEOUT_NS = 2_000_000_000L",
        "HEARTBEAT_TIMEOUT_NS = 1_500_000_000L",
        "REQUIRED_SAFETY_CAPABILITIES",
        "required_capability_missing",
    ):
        if required not in control:
            errors.append(f"control contract token missing: {required}")
    main = (root / "app/src/main/java/com/trollhunter/xglasses/MainActivity.kt").read_text(
        encoding="utf-8"
    )
    if "ControlState.READY -> UsbState.READY" not in main:
        errors.append("Android READY must come from the control session")
    for required in (
        "NavigationCoordinator",
        "RequestMultiplePermissions",
        "startNavigation",
        "navigationMustStop",
        "!navigationState.providerConfigured",
    ):
        if required not in main:
            errors.append(f"navigation activity token missing: {required}")
    ui = (root / "app/src/main/java/com/trollhunter/xglasses/ui/XGlassesApp.kt").read_text(
        encoding="utf-8"
    )
    for required in (
        "重复上一条提示",
        "heightIn(min = 64.dp)",
        "liveRegion",
        "搜索目的地",
        "开始步行导航",
        "地图路线不是道路安全证明",
    ):
        if required not in ui:
            errors.append(f"accessibility contract token missing: {required}")
    navigation = (
        root / "app/src/main/java/com/trollhunter/xglasses/navigation/NavigationEngine.kt"
    ).read_text(encoding="utf-8")
    for required in ("REROUTE_REQUIRED", "location_unusable", "offRouteConfirmations"):
        if required not in navigation:
            errors.append(f"navigation safety token missing: {required}")
    provider = (
        root / "app/src/main/java/com/trollhunter/xglasses/navigation/OpenNavigationProvider.kt"
    ).read_text(encoding="utf-8")
    for required in (
        'uri.scheme == "https"',
        "1_048_576",
        '"pedestrian"',
        '"non-pedestrian route rejected"',
        '"route provider reported failure"',
    ):
        if required not in provider:
            errors.append(f"navigation provider token missing: {required}")
    golden = (
        root / "app/src/test/java/com/trollhunter/xglasses/protocol/XgProtocolTest.kt"
    ).read_text(encoding="utf-8")
    if "26184fbc616263c2412435" not in golden:
        errors.append("Python/firmware golden packet suffix missing")
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
