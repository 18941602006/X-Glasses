"""Static cross-language contract checks; compile and hardware tests are separate gates."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.common.control import CAP_CLOCK, CAP_HAPTIC  # noqa: E402
from server.common.protocol import HEADER_SIZE, MAX_PAYLOAD, MAX_WIRE, VERSION  # noqa: E402

FILES = (
    "CMakeLists.txt",
    "sdkconfig.defaults",
    "main/CMakeLists.txt",
    "main/idf_component.yml",
    "main/main.c",
    "main/xg_protocol.h",
    "main/xg_protocol.c",
    "main/xg_controller.h",
    "main/xg_controller.c",
)


def check(root: Path) -> list[str]:
    errors = []
    contents = {}
    for relative in FILES:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing firmware file: {relative}")
            continue
        contents[relative] = path.read_text(encoding="utf-8")

    header = contents.get("main/xg_protocol.h", "")
    expected = {
        "#define XG_VERSION": VERSION,
        "#define XG_MAX_PAYLOAD": MAX_PAYLOAD,
        "#define XG_HEADER_SIZE": HEADER_SIZE,
        "#define XG_MAX_WIRE": MAX_WIRE,
    }
    for label, value in expected.items():
        if f"{label} {value}u" not in header:
            errors.append(f"Python/C contract mismatch: {label}")

    controller = contents.get("main/xg_controller.h", "")
    for label, value in (("XG_CAP_CLOCK", CAP_CLOCK), ("XG_CAP_HAPTIC", CAP_HAPTIC)):
        bit = value.bit_length() - 1
        if f"#define {label} (1u << {bit})" not in controller:
            errors.append(f"Python/C capability mismatch: {label}")

    manifest = contents.get("main/idf_component.yml", "")
    for pin in (
        'idf: "==5.5.4"',
        'espressif/esp_tinyusb: "==2.2.1"',
        'espressif/esp32-camera: "==2.1.7"',
    ):
        if pin not in manifest:
            errors.append(f"missing exact component pin: {pin}")

    config = contents.get("sdkconfig.defaults", "")
    for setting in ("CONFIG_TINYUSB_CDC_ENABLED=y", "CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y"):
        if setting not in config:
            errors.append(f"missing safe USB setting: {setting}")
    if "CONFIG_ESP_CONSOLE_USB_CDC=y" in config:
        errors.append("application CDC must not be the text log console")

    runtime = "\n".join(contents.get(name, "") for name in FILES if name.endswith((".c", ".h")))
    for excluded in ("blindpath", "crosswalk", "zebra", "slam", "WiFi.h"):
        if excluded.lower() in runtime.lower():
            errors.append(f"excluded runtime feature found: {excluded}")
    if "xg_controller_init(&controller, boot_id, XG_CAP_CLOCK," not in runtime:
        errors.append("unverified device capabilities must default to CLOCK only")
    if "0xEDB88320u" not in runtime:
        errors.append("C CRC-32 polynomial missing")
    return errors


def main() -> int:
    errors = check(ROOT / "firmware")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print(
        "PASS: firmware files, exact component pins, Python/C constants, and disabled capability scope"
    )
    print(
        "Not checked: compilation, USB enumeration, peripherals, power, timing, or hardware safety."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
