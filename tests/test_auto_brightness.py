"""Check the auto-brightness curve and how manual changes are respected."""
from importlib.machinery import SourceFileLoader
from pathlib import Path
import unittest

AB = SourceFileLoader("auto_brightness", str(Path(__file__).resolve().parents[1] / "scripts/macbook-t1-auto-brightness")).load_module()
CURVE = AB.parse_curve(AB.DEFAULT_CURVE)


def settle(controller, lux, current, ticks=20):
    for _ in range(ticks):
        want = controller.step(lux, current, CURVE)
        if want is not None:
            current = want
    return current


class Curve(unittest.TestCase):
    def test_points(self):
        self.assertEqual(AB.target_pct(0, CURVE), 1)
        self.assertAlmostEqual(AB.target_pct(150, CURVE), 40)
        self.assertEqual(AB.target_pct(5000, CURVE), 100)
        self.assertTrue(1 < AB.target_pct(10, CURVE) < 40)

    def test_bad_curve_falls_back(self):
        self.assertEqual(AB.parse_curve("nonsense"), CURVE)


class Controller(unittest.TestCase):
    def test_follows_light(self):
        c = AB.Controller(1023)
        self.assertAlmostEqual(settle(c, 150, 1023) / 1023 * 100, 40, delta=3)
        self.assertLess(settle(c, 0, 409), 20)

    def test_small_difference_ignored(self):
        c = AB.Controller(1023)
        self.assertIsNone(c.step(150, 420, CURVE))   # 41% vs 40%

    def test_manual_change_sets_ratio(self):
        c = AB.Controller(1023)
        cur = settle(c, 150, 409)
        cur = 818                                      # user doubles brightness
        self.assertIsNone(c.step(150, cur, CURVE))
        self.assertAlmostEqual(c.ratio, 2, delta=0.1)
        self.assertGreater(settle(c, 40, cur), settle(AB.Controller(1023), 40, 409))

    def test_fine_steps_below_one_percent_left_alone(self):
        c = AB.Controller(1023)
        settle(c, 150, 409)
        self.assertIsNone(c.step(150, 6, CURVE))      # user went to 0.6%
        for _ in range(10):
            self.assertIsNone(c.step(1000, 6, CURVE))


if __name__ == "__main__":
    unittest.main()
