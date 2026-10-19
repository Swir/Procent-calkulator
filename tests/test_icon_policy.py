import tempfile
import unittest
from pathlib import Path
from app_identity import resolve_icon

class IconPolicyTests(unittest.TestCase):
    def test_missing_custom_icon_uses_swirui(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "swirui.ico").write_bytes(b"fallback")
            self.assertEqual(resolve_icon(root), root / "swirui.ico")

    def test_custom_application_icon_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "swirui.ico").write_bytes(b"fallback")
            (root / "app.ico").write_bytes(b"application")
            self.assertEqual(resolve_icon(root), root / "app.ico")

    def test_missing_both_icons_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                resolve_icon(directory)

    def test_packaged_fallback_has_small_and_large_frames(self):
        from PIL import Image
        with Image.open(resolve_icon()) as icon:
            self.assertTrue({(16, 16), (32, 32), (48, 48), (256, 256)} <= icon.ico.sizes())

if __name__ == "__main__":
    unittest.main()
