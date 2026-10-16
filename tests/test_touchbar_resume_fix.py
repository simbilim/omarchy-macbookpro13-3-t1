"""Check safe source migration before a driver rebuild is allowed."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/macbook-t1-touchbar-resume-fix"
PATCH = SCRIPT.read_text().split("python3 - <<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
TRANSFER = """\t\t} while (++tries < 5);
\t} else {
\t\trc = hid_hw_raw_request(tb_dev->mode_iface.hdev, report->id,"""
NORMALIZED_TRANSFER = """\t\t} while (++tries < 5);

\t\t/* usb_control_msg returns bytes; the worker expects zero on success. */
\t\tif (rc >= 0)
\t\t\trc = (rc == 1) ? 0 : -EIO;
\t} else {
\t\trc = hid_hw_raw_request(tb_dev->mode_iface.hdev, report->id,"""
ORIGINAL = TRANSFER + """
static int appletb_reset_resume(struct hid_device *hdev)
{
\tif ((tb_dev->mode_iface.hdev && !tb_dev->mode_iface.suspended) &&
\t    (tb_dev->disp_iface.hdev && !tb_dev->disp_iface.suspended)) {
\t\ttb_dev->active = true;
\t\ttb_dev->restore_autopm = true;
\t}
\treturn 0;
}
#endif

static struct appletb_device *appletb_alloc_device(void) {}
static struct hid_driver appletb_driver = {
\t.suspend = appletb_suspend,
\t.reset_resume = appletb_reset_resume,
};
"""


class ResumeFixTests(unittest.TestCase):
    def apply(self, root, source):
        path = root / "apple-touchbar.c"
        path.write_text(source)
        patch = PATCH.replace("'/usr/src/apple-ib-drv-0.1/apple-touchbar.c'", repr(str(path)))
        patch = patch.replace("'/var/lib/macbook-t1-omarchy'", repr(str(root)))
        result = subprocess.run([sys.executable, "-c", patch], capture_output=True, text=True)
        return result, path.read_text()

    def test_original_alias_and_idempotence(self):
        for alias in ("", "\t.resume = appletb_reset_resume,\n"):
            with self.subTest(alias=bool(alias)), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                original = ORIGINAL.replace("\t.reset_resume =", alias + "\t.reset_resume =")
                result, fixed = self.apply(root, original)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("\t.resume = appletb_resume,", fixed)
                self.assertIn("tb_dev->is_t1 ||", fixed)
                self.assertIn("appletb_resume_common(hdev, false)", fixed)
                self.assertIn("appletb_resume_common(hdev, true)", fixed)
                self.assertIn(NORMALIZED_TRANSFER, fixed)
                (root / "pending-touchbar-rebuild").unlink()
                result, second = self.apply(root, fixed)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(second, fixed)
                self.assertFalse((root / "pending-touchbar-rebuild").exists())

    def test_upgrade_from_callback_only_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, fixed = self.apply(root, ORIGINAL)
            old_local = fixed.replace("(tb_dev->is_t1 ||\n\t     (tb_dev->disp_iface.hdev && !tb_dev->disp_iface.suspended)))", "(tb_dev->disp_iface.hdev && !tb_dev->disp_iface.suspended))")
            self.assertNotEqual(old_local, fixed)
            result, upgraded = self.apply(root, old_local)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(upgraded, fixed)

    def test_unexpected_source_stays_untouched(self):
        for source in (ORIGINAL.replace(".suspend =", ".resume = upstream_resume,\n\t.suspend ="), ORIGINAL.replace("disp_iface.suspended", "unexpected_state"), ORIGINAL.replace(TRANSFER, "unknown transfer"), ORIGINAL + TRANSFER):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                result, unchanged = self.apply(root, source)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(unchanged, source)
                self.assertFalse((root / "pending-touchbar-rebuild").exists())

    def test_upgrade_from_resume_fix_with_bad_transfer_return(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, fixed = self.apply(root, ORIGINAL)
            old_local = fixed.replace(NORMALIZED_TRANSFER, TRANSFER)
            self.assertNotEqual(old_local, fixed)
            result, upgraded = self.apply(root, old_local)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(upgraded, fixed)


if __name__ == "__main__":
    unittest.main()
