"""Reject the observed all-ones PMC reading without losing battery evidence."""
from pathlib import Path
import subprocess
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/macbook-sleep-diagnostics"


class SleepDiagnosticsTests(unittest.TestCase):
    def cycle(self, before, after, before_status="Discharging", after_status="Discharging",
              after_charge=5999000):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def write(path, value):
                dest = root / path.lstrip("/")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(str(value) + "\n")

            source = SCRIPT.read_text().replace("[[ $EUID == 0 ]] || exit 1", ":")
            for prefix in ("/sys/", "/proc/", "/run/"):
                source = source.replace(prefix, str(root) + prefix)
            script = root / "diagnostics"
            script.write_text(source)
            write("/sys/class/dmi/id/product_name", "MacBookPro13,3")
            battery = "/sys/class/power_supply/BAT0/"
            for key, value in {"status": before_status, "charge_now": 6000000,
                               "voltage_now": 12000000}.items():
                write(battery + key, value)
            counter = "/sys/kernel/debug/pmc_core/slp_s0_residency_usec"
            packages = "/sys/kernel/debug/pmc_core/package_cstate_show"
            warning = "/sys/module/intel_pmc_core/parameters/warn_on_s0ix_failures"
            write(counter, before)
            write(packages, "Package C3 : 1000\nPackage C6 : 0")
            write(warning, "N")
            pre = subprocess.run(["bash", str(script), "pre", "suspend"],
                                 capture_output=True, text=True, check=True)
            armed = (root / warning.lstrip("/")).read_text().strip()
            write("/run/macbook-sleep-diagnostics/epoch", int(time.time()) - 10)
            write(counter, after)
            write(packages, "Package C3 : 9000\nPackage C6 : 0")
            write(battery + "charge_now", after_charge)
            write(battery + "status", after_status)
            post = subprocess.run(["bash", str(script), "post", "suspend"],
                                  capture_output=True, text=True, check=True)
            self.assertEqual((root / warning.lstrip("/")).read_text().strip(), "N")
            self.assertFalse((root / "run/macbook-sleep-diagnostics").exists())
            self.assertIn(f"charge_delta_uAh={6000000-after_charge}", post.stdout)
            self.assertIn("C3=8000", post.stdout)
            return pre.stdout + post.stdout, armed

    def test_invalid_counter_does_not_report_zero_percent(self):
        output, armed = self.cycle(446676598680, 446676598680)
        self.assertIn("unavailable (invalid PMC counter", output)
        self.assertNotIn("residency_pct=", output)
        self.assertEqual(armed, "N")

    def test_counter_becoming_invalid_on_resume(self):
        output, _ = self.cycle(104000, 446676598680)
        self.assertIn("unavailable (invalid PMC counter", output)
        self.assertNotIn("residency_pct=", output)

    def test_valid_zero_and_progressing_counters(self):
        for after, delta in ((104000, 0), (1104000, 1000000)):
            with self.subTest(after=after):
                output, armed = self.cycle(104000, after)
                self.assertIn(f"delta_us={delta} residency_pct=", output)
                self.assertNotIn("unavailable (invalid PMC counter", output)
                self.assertEqual(armed, "Y")

    def test_power_reconnected_before_post_invalidates_watts(self):
        output, _ = self.cycle(104000, 1104000, after_status="Charging")
        self.assertIn("power estimate unavailable", output)
        self.assertNotIn("estimated_avg_W=", output)

    def test_charging_at_entry_or_increased_charge_invalidates_watts(self):
        for kwargs in ({"before_status": "Charging"}, {"after_charge": 6001000}):
            with self.subTest(**kwargs):
                output, _ = self.cycle(104000, 1104000, **kwargs)
                self.assertIn("power estimate unavailable", output)
                self.assertNotIn("estimated_avg_W=", output)


if __name__ == "__main__":
    unittest.main()
