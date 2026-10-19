"""Compare the sounds a word should have with the sounds a child actually said.

Everything here is plain Python with no model, so it can be tested anywhere.
Phonemes are IPA strings, one per sound, e.g. "rainbow" -> ["ɹ", "eɪ", "n", "b", "oʊ"].
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Marks that change how a sound is written but not which sound it is.
_STRIP = "ˈˌːˑ͜͡"
# Different spellings of the same sound, mapped to one form.
_SAME = {
    "r": "ɹ",
    "ɾ": "t",  # American "butter" flap counts as t
    "ɐ": "ʌ",
    "ᵻ": "ɪ",
    "ɚ": "ɝ",
    "əl": "l",
    "o": "oʊ",
    "e": "eɪ",
    "g": "ɡ",
}

# Common speech-sound patterns therapists look for, as (expected, said) -> name.
# These are standard terms for childhood speech errors.
PATTERNS = {
    ("ɹ", "w"): "gliding (r said as w)",
    ("l", "w"): "gliding (l said as w)",
    ("ɹ", "j"): "gliding (r said as y)",
    ("l", "j"): "gliding (l said as y)",
    ("s", "θ"): "lisp (s said as th)",
    ("z", "ð"): "lisp (z said as th)",
    ("k", "t"): "fronting (k said as t)",
    ("ɡ", "d"): "fronting (g said as d)",
    ("ʃ", "s"): "fronting (sh said as s)",
    ("s", "t"): "stopping (s said as t)",
    ("z", "d"): "stopping (z said as d)",
    ("f", "p"): "stopping (f said as p)",
    ("v", "b"): "stopping (v said as b)",
    ("θ", "f"): "th said as f",
    ("ð", "d"): "th said as d",
    ("θ", "t"): "th said as t",
    ("tʃ", "ʃ"): "ch said as sh",
}


# The wav2vec model sometimes writes vowels in a tone-numbered style from its other languages ("ei5").
_DIPHTHONGS = {"ei": "eɪ", "ou": "oʊ", "ai": "aɪ", "au": "aʊ", "oi": "ɔɪ"}


def normalize(ph: str) -> str:
    for ch in _STRIP:
        ph = ph.replace(ch, "")
    ph = ph.rstrip("0123456789")
    ph = _DIPHTHONGS.get(ph, ph)
    return _SAME.get(ph, ph)


def clean(phonemes: list[str]) -> list[str]:
    out = [normalize(p) for p in phonemes]
    return [p for p in out if p]


@dataclass
class Step:
    """One position in the alignment."""

    op: str  # "ok", "swap" (said a different sound), "missing" (left out), "extra" (added)
    expected: str | None
    said: str | None

    @property
    def pattern(self) -> str | None:
        if self.op == "swap":
            return PATTERNS.get((self.expected, self.said))
        return None


@dataclass
class Result:
    word: str
    expected: list[str]
    said: list[str]
    steps: list[Step] = field(default_factory=list)
    target: str | None = None

    @property
    def errors(self) -> list[Step]:
        return [s for s in self.steps if s.op != "ok"]

    @property
    def accuracy(self) -> float:
        """Share of expected sounds said correctly (0-1)."""
        if not self.expected:
            return 0.0
        ok = sum(1 for s in self.steps if s.op == "ok")
        return ok / len(self.expected)

    @property
    def target_ok(self) -> bool | None:
        """Whether every place the target sound should appear was said right. None if no target."""
        if not self.target:
            return None
        spots = [s for s in self.steps if s.expected == self.target]
        if not spots:
            return None
        return all(s.op == "ok" for s in spots)

    def clear(self, min_accuracy: float = 0.8) -> bool:
        """A "clear try". With a target sound, like a therapist scores it: the target sound is right.
        Other sounds can vary (accents, vowels) without failing the try. Without a target: most sounds right."""
        if self.target_ok is not None:
            return self.target_ok
        return self.accuracy >= min_accuracy

    def explain(self) -> str:
        lines = [
            f"Word:      {self.word}",
            f"Expected:  {' '.join(self.expected)}",
            f"Heard:     {' '.join(self.said) or '(nothing)'}",
            f"Accuracy:  {round(self.accuracy * 100)}%",
        ]
        if self.target:
            t = self.target_ok
            lines.append(f"Target {self.target}: {'not in word' if t is None else 'right' if t else 'WRONG'}")
        for s in self.errors:
            if s.op == "swap":
                note = f" -> {s.pattern}" if s.pattern else ""
                lines.append(f"  said {s.said} instead of {s.expected}{note}")
            elif s.op == "missing":
                lines.append(f"  left out {s.expected}")
            else:
                lines.append(f"  added {s.said}")
        lines.append(f"Clear try: {'yes' if self.clear() else 'no'}")
        return "\n".join(lines)


def align(expected: list[str], said: list[str]) -> list[Step]:
    """Line up two phoneme lists with the fewest changes (edit distance), then read off the steps."""
    n, m = len(expected), len(said)
    cost = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        cost[i][0] = i
    for j in range(1, m + 1):
        cost[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            same = expected[i - 1] == said[j - 1]
            cost[i][j] = min(
                cost[i - 1][j - 1] + (0 if same else 1),
                cost[i - 1][j] + 1,
                cost[i][j - 1] + 1,
            )
    steps: list[Step] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            same = expected[i - 1] == said[j - 1]
            if cost[i][j] == cost[i - 1][j - 1] + (0 if same else 1):
                steps.append(Step("ok" if same else "swap", expected[i - 1], said[j - 1]))
                i, j = i - 1, j - 1
                continue
        if i > 0 and cost[i][j] == cost[i - 1][j] + 1:
            steps.append(Step("missing", expected[i - 1], None))
            i -= 1
        else:
            steps.append(Step("extra", None, said[j - 1]))
            j -= 1
    steps.reverse()
    return steps


def compare(word: str, expected: list[str], said: list[str], target: str | None = None) -> Result:
    e, s = clean(expected), clean(said)
    return Result(word=word, expected=e, said=s, steps=align(e, s), target=normalize(target) if target else None)
