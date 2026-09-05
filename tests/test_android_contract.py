import shutil
import tempfile
import unittest
from pathlib import Path

from tools.check_android_contract import ANDROID, check


class AndroidContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "android"
        shutil.copytree(ANDROID, self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_current_android_contract(self):
        self.assertEqual(check(self.root), [])

    def test_missing_file(self):
        (self.root / "settings.gradle.kts").unlink()
        self.assertIn("missing Android file: settings.gradle.kts", check(self.root))

    def test_background_location_permission_is_rejected(self):
        manifest = self.root / "app/src/main/AndroidManifest.xml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "<application",
                '<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />\n<application',
            ),
            encoding="utf-8",
        )
        self.assertIn("unexpected permission: ACCESS_BACKGROUND_LOCATION", check(self.root))

    def test_navigation_permissions_and_safety_contract_are_required(self):
        manifest = self.root / "app/src/main/AndroidManifest.xml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                '<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />\n', ""
            ),
            encoding="utf-8",
        )
        engine = (
            self.root / "app/src/main/java/com/trollhunter/xglasses/navigation/NavigationEngine.kt"
        )
        engine.write_text(
            engine.read_text(encoding="utf-8").replace("location_unusable", "location_removed"),
            encoding="utf-8",
        )
        errors = check(self.root)
        self.assertIn("required navigation permission missing: ACCESS_FINE_LOCATION", errors)
        self.assertIn("navigation safety token missing: location_unusable", errors)

    def test_navigation_stops_on_link_loss(self):
        main = self.root / "app/src/main/java/com/trollhunter/xglasses/MainActivity.kt"
        main.write_text(
            main.read_text(encoding="utf-8").replace("navigationMustStop", "stopRuleRemoved"),
            encoding="utf-8",
        )
        self.assertIn(
            "navigation activity token missing: navigationMustStop",
            check(self.root),
        )

    def test_removed_task_and_installed_default_are_rejected(self):
        state = self.root / "app/src/main/java/com/trollhunter/xglasses/domain/AppState.kt"
        text = state.read_text(encoding="utf-8").replace("LOCATE_GRASP", "LOCATE_REMOVED")
        text = text.replace("RuntimeState.NOT_INSTALLED", "RuntimeState.AVAILABLE")
        state.write_text(text, encoding="utf-8")
        errors = check(self.root)
        self.assertIn("missing task: LOCATE_GRASP", errors)
        self.assertIn("safe default runtime/monitoring state missing", errors)

    def test_crossing_permission_and_floating_dependency_are_rejected(self):
        ui = self.root / "app/src/main/java/com/trollhunter/xglasses/ui/XGlassesApp.kt"
        ui.write_text(
            ui.read_text(encoding="utf-8") + '\nconst val BAD = "可以过街"\n',
            encoding="utf-8",
        )
        gradle = self.root / "app/build.gradle.kts"
        gradle.write_text(
            gradle.read_text(encoding="utf-8").replace(
                "androidx.core:core-ktx:1.16.0", "androidx.core:core-ktx:+"
            ),
            encoding="utf-8",
        )
        errors = check(self.root)
        self.assertIn("forbidden Android source term: 可以过街", errors)
        self.assertIn("floating Android dependency", errors)

    def test_hardcoded_usb_device_is_rejected(self):
        usb = self.root / "app/src/main/java/com/trollhunter/xglasses/usb/UsbSessionManager.kt"
        usb.write_text(
            usb.read_text(encoding="utf-8") + "\n// vendorId == 0x303a\n",
            encoding="utf-8",
        )
        self.assertIn(
            "USB device must be user-selected until VID/PID is frozen",
            check(self.root),
        )

    def test_ready_repeat_and_golden_contracts_are_required(self):
        main = self.root / "app/src/main/java/com/trollhunter/xglasses/MainActivity.kt"
        main.write_text(
            main.read_text(encoding="utf-8").replace(
                "ControlState.READY -> UsbState.READY",
                "ControlState.READY -> UsbState.FAILED",
            ),
            encoding="utf-8",
        )
        state = self.root / "app/src/main/java/com/trollhunter/xglasses/domain/AppState.kt"
        state.write_text(
            state.read_text(encoding="utf-8").replace("RepeatLastOutput", "RepeatRemoved"),
            encoding="utf-8",
        )
        golden = self.root / "app/src/test/java/com/trollhunter/xglasses/protocol/XgProtocolTest.kt"
        golden.write_text(
            golden.read_text(encoding="utf-8").replace(
                "26184fbc616263c2412435", "00000000616263c2412435"
            ),
            encoding="utf-8",
        )
        errors = check(self.root)
        self.assertIn("Android READY must come from the control session", errors)
        self.assertIn("repeat action missing", errors)
        self.assertIn("Python/firmware golden packet suffix missing", errors)


if __name__ == "__main__":
    unittest.main()
