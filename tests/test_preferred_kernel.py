"""Boot-config regression checks with synthetic, non-private EFI contents."""
import hashlib
from pathlib import Path
import runpy
import unittest

render = runpy.run_path(str(Path(__file__).parents[1] / "scripts/macbook-t1-preferred-kernel"))["render"]


def config(image, rescue=b"rescue-image"):
    digest = hashlib.blake2b(image).hexdigest()
    rescue_digest = hashlib.blake2b(rescue).hexdigest()
    return f"""timeout: 1
default_entry: 2

/Omarchy Rescue - Console
    protocol: efi
    path: boot():/EFI/Linux/omarchy_linux.efi#{rescue_digest}
/Omarchy Rescue - Safe Graphics
    protocol: efi
    path: boot():/EFI/Linux/omarchy_linux-omarchy.efi#{rescue_digest}
/+Omarchy
    //linux-lts
        protocol: efi
        path: boot():/EFI/Linux/omarchy_linux-lts.efi#{digest}
        cmdline: preserved-test-options
    //linux
        protocol: efi
        path: boot():/ordinary.efi#original-integrity-check
    //+Snapshots
        ///snapshot
            ////linux-lts
                protocol: efi
                path: boot():/snapshot.efi#original-integrity-check
"""


class PreferredKernelTest(unittest.TestCase):
    def test_update_keeps_generated_entries_and_is_idempotent(self):
        original = config(b"image-one")
        updated = render(original, b"image-one", b"rescue-image")
        self.assertEqual(render(updated, b"image-one", b"rescue-image"), updated)
        self.assertIn("default_entry: 1\n", updated)
        self.assertEqual(updated.count("/Omarchy LTS - MacBook\n"), 1)
        rescue_path = "boot():/EFI/Linux/omarchy_linux-omarchy.efi#" + hashlib.blake2b(b"rescue-image").hexdigest()
        self.assertEqual(updated.count(rescue_path), 2)

    def test_rewrite_without_markers_refreshes_stale_preferred_hash(self):
        previous = render(config(b"old-image"), b"old-image", b"rescue-image")
        previous = "\n".join(line for line in previous.split("\n") if not line.startswith("#"))
        start = previous.index("/+Omarchy")
        generated = "/+Omarchy" + config(b"new-image").split("/+Omarchy", 1)[1]
        rewritten = previous[:start] + generated
        updated = render(rewritten, b"new-image", b"rescue-image")
        self.assertNotIn(hashlib.blake2b(b"old-image").hexdigest(), updated)
        self.assertEqual(updated.count("/Omarchy LTS - MacBook\n"), 1)

    def test_refuses_unverified_or_ambiguous_boot_data(self):
        cases = [
            config(b"other-image"),
            config(b"image").replace("//linux-lts", "//linux-missing"),
            config(b"image") + "\n    //linux-lts\n        protocol: efi\n",
            config(b"image").replace("default_entry: 2\n", ""),
            config(b"image").replace("        cmdline: preserved-test-options", ""),
        ]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    render(text, b"image", b"rescue-image")

    def test_refuses_missing_or_unexpected_rescue_entries(self):
        cases = [
            config(b"image").replace("/Omarchy Rescue - Console", "/Other"),
            config(b"image").replace(
                "boot():/EFI/Linux/omarchy_linux.efi#",
                "boot():/EFI/Linux/unmanaged.efi#",
                1,
            ),
        ]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    render(text, b"image", b"rescue-image")


if __name__ == "__main__":
    unittest.main()
