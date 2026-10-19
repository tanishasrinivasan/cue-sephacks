"""Measure how often a backend agrees with a human about whether a try was clear.

Make a CSV like recordings.example.csv (one row per recording, judged by a person, ideally a
speech therapist), then:

    python evaluate.py recordings.csv --backend wav2vec
    python evaluate.py recordings.csv --backend azure

This is how to decide between approaches, and when to stop and train a model: if no backend
catches most real mistakes without flagging most good tries, it's time to fine-tune.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass

from align import compare


@dataclass
class Score:
    caught: int = 0  # unclear tries the backend flagged (good)
    missed: int = 0  # unclear tries it said were fine (bad: the kid isn't corrected)
    false_alarm: int = 0  # clear tries it flagged (bad: the kid is told they're wrong when they weren't)
    passed: int = 0  # clear tries it said were fine (good)

    def add(self, human_clear: bool, model_clear: bool):
        if human_clear and model_clear:
            self.passed += 1
        elif human_clear:
            self.false_alarm += 1
        elif model_clear:
            self.missed += 1
        else:
            self.caught += 1

    def report(self) -> str:
        total = self.caught + self.missed + self.false_alarm + self.passed
        bad = self.caught + self.missed
        good = self.passed + self.false_alarm
        pct = lambda a, b: f"{round(100 * a / b)}%" if b else "n/a"
        return "\n".join(
            [
                f"Recordings:          {total}",
                f"Agrees with human:   {pct(self.caught + self.passed, total)}",
                f"Mistakes caught:     {pct(self.caught, bad)}  ({self.caught} of {bad})",
                f"Good tries flagged:  {pct(self.false_alarm, good)}  ({self.false_alarm} of {good})",
            ]
        )


def main():
    from backends import expected_phonemes, make, target_sound

    p = argparse.ArgumentParser()
    p.add_argument("csv", help="columns: file, word, target, clear (yes/no)")
    p.add_argument("--backend", default="wav2vec", choices=["wav2vec", "azure"])
    p.add_argument("--min-accuracy", type=float, default=0.8)
    a = p.parse_args()

    backend = make(a.backend)
    score = Score()
    with open(a.csv, newline="") as f:
        for row in csv.DictReader(f):
            r = compare(row["word"], expected_phonemes(row["word"]), backend.heard(row["file"], row["word"]),
                        target_sound(row.get("target")))
            human = row["clear"].strip().lower() in ("yes", "y", "1", "true")
            model = r.clear(a.min_accuracy)
            score.add(human, model)
            mark = "" if human == model else "   <-- disagrees"
            print(f"{row['file']}: human {'clear' if human else 'unclear'}, "
                  f"model {'clear' if model else 'unclear'} (heard {' '.join(r.said)}){mark}")
    print()
    print(score.report())


if __name__ == "__main__":
    main()
