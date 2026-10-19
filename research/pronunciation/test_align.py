"""Run with: python -m unittest test_align  (from this folder). No model or internet needed."""

import unittest

from align import compare, normalize

RAINBOW = ["ɹ", "eɪ", "n", "b", "oʊ"]


class TestAlign(unittest.TestCase):
    def test_correct_word(self):
        r = compare("rainbow", RAINBOW, ["ɹ", "eɪ", "n", "b", "oʊ"], target="ɹ")
        self.assertEqual(r.accuracy, 1.0)
        self.assertTrue(r.target_ok)
        self.assertTrue(r.clear())
        self.assertEqual(r.errors, [])

    def test_gliding_is_named(self):
        r = compare("rainbow", RAINBOW, ["w", "eɪ", "n", "b", "oʊ"], target="ɹ")
        self.assertFalse(r.target_ok)
        self.assertFalse(r.clear())  # 80% of sounds right, but the target sound is wrong
        [err] = r.errors
        self.assertEqual((err.op, err.expected, err.said), ("swap", "ɹ", "w"))
        self.assertEqual(err.pattern, "gliding (r said as w)")

    def test_other_sound_slip_still_clear_if_target_right(self):
        # "rainbo" with a slightly different vowel at the end: target r is fine
        r = compare("rainbow", RAINBOW, ["ɹ", "eɪ", "n", "b", "ʌ"], target="ɹ")
        self.assertTrue(r.target_ok)
        self.assertTrue(r.clear())

    def test_missing_and_extra_sounds(self):
        # "spoon" said as "poon" (cluster reduction) and "spoon" with an extra sound
        spoon = ["s", "p", "u", "n"]
        r = compare("spoon", spoon, ["p", "u", "n"], target="s")
        self.assertEqual([(s.op, s.expected) for s in r.errors], [("missing", "s")])
        self.assertFalse(r.target_ok)
        r2 = compare("spoon", spoon, ["s", "ə", "p", "u", "n"])
        self.assertEqual([(s.op, s.said) for s in r2.errors], [("extra", "ə")])

    def test_lisp(self):
        r = compare("sun", ["s", "ʌ", "n"], ["θ", "ʌ", "n"], target="s")
        self.assertEqual(r.errors[0].pattern, "lisp (s said as th)")

    def test_spelling_variants_match(self):
        # Stress marks, length marks and r-spellings shouldn't count as errors
        self.assertEqual(normalize("ˈɹ"), "ɹ")
        self.assertEqual(normalize("iː"), "i")
        r = compare("red", ["ɹ", "ɛ", "d"], ["r", "ˈɛ", "d"], target="r")
        self.assertEqual(r.accuracy, 1.0)

    def test_model_tone_style_vowels(self):
        # The model sometimes writes "ei5" for eɪ; it shouldn't throw off the alignment
        self.assertEqual(normalize("ei5"), "eɪ")
        r = compare("rainbow", RAINBOW, ["w", "ei5", "n", "b", "ou5"], target="ɹ")
        [err] = r.errors
        self.assertEqual((err.expected, err.said, err.pattern), ("ɹ", "w", "gliding (r said as w)"))

    def test_vowel_differences_dont_fail_a_target_try(self):
        # "sun" with a different vowel (accent): the s is right, so it's a clear try
        r = compare("sun", ["s", "ʌ", "n"], ["s", "ɔ", "n"], target="s")
        self.assertTrue(r.clear())

    def test_nothing_heard(self):
        r = compare("red", ["ɹ", "ɛ", "d"], [], target="ɹ")
        self.assertEqual(r.accuracy, 0.0)
        self.assertFalse(r.clear())

    def test_target_not_in_word(self):
        r = compare("sun", ["s", "ʌ", "n"], ["s", "ʌ", "n"], target="ɹ")
        self.assertIsNone(r.target_ok)
        self.assertTrue(r.clear())


if __name__ == "__main__":
    unittest.main()
