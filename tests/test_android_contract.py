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

    def test_privacy_permissions_are_rejected(self):
        manifest = self.root / "app/src/main/AndroidManifest.xml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "<application",
                '<uses-permission android:name="android.permission.INTERNET" />\n<application',
            ),
            encoding="utf-8",
        )
        self.assertIn("unexpected permission: INTERNET", check(self.root))

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


if __name__ == "__main__":
    unittest.main()
