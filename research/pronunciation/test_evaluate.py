import unittest

from evaluate import Score


class TestScore(unittest.TestCase):
    def test_counts(self):
        s = Score()
        s.add(human_clear=False, model_clear=False)  # caught
        s.add(human_clear=False, model_clear=True)  # missed
        s.add(human_clear=True, model_clear=False)  # false alarm
        s.add(human_clear=True, model_clear=True)  # passed
        s.add(human_clear=True, model_clear=True)  # passed
        self.assertEqual((s.caught, s.missed, s.false_alarm, s.passed), (1, 1, 1, 2))
        text = s.report()
        self.assertIn("Recordings:          5", text)
        self.assertIn("Agrees with human:   60%", text)
        self.assertIn("Mistakes caught:     50%  (1 of 2)", text)
        self.assertIn("Good tries flagged:  33%  (1 of 3)", text)


if __name__ == "__main__":
    unittest.main()
