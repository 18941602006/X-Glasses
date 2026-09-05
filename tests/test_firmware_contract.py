"""Positive and negative tests for the static firmware contract checker."""

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.check_firmware_contract import check


class FirmwareContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "firmware"
        source = Path(__file__).resolve().parents[1] / "firmware"
        shutil.copytree(source, self.root)

    def replace(self, relative, before, after):
        path = self.root / relative
        path.write_text(path.read_text(encoding="utf-8").replace(before, after), encoding="utf-8")

    def test_current_firmware_contract(self):
        self.assertEqual(check(self.root), [])

    def test_missing_file(self):
        (self.root / "main/xg_protocol.h").unlink()
        self.assertTrue(any("missing firmware" in error for error in check(self.root)))

    def test_protocol_constant_drift(self):
        self.replace("main/xg_protocol.h", "XG_MAX_PAYLOAD 4096u", "XG_MAX_PAYLOAD 8192u")
        self.assertTrue(any("contract mismatch" in error for error in check(self.root)))

    def test_floating_component_version(self):
        self.replace("main/idf_component.yml", "==2.2.1", "^2.2.1")
        self.assertTrue(any("component pin" in error for error in check(self.root)))

    def test_cdc_text_log_collision(self):
        path = self.root / "sdkconfig.defaults"
        path.write_text(
            path.read_text(encoding="utf-8") + "CONFIG_ESP_CONSOLE_USB_CDC=y\n", encoding="utf-8"
        )
        self.assertTrue(any("text log" in error for error in check(self.root)))

    def test_unverified_haptic_capability_rejected(self):
        self.replace("main/main.c", "XG_CAP_CLOCK,", "XG_CAP_CLOCK | XG_CAP_HAPTIC,")
        self.assertTrue(any("CLOCK only" in error for error in check(self.root)))

    def test_excluded_feature_rejected(self):
        path = self.root / "main/main.c"
        path.write_text(path.read_text(encoding="utf-8") + "// crosswalk\n", encoding="utf-8")
        self.assertTrue(any("excluded runtime" in error for error in check(self.root)))


if __name__ == "__main__":
    unittest.main()
