"""Test the checker on real kids' "r" words from the PERCEPT-R corpus (TalkBank / PhonBank).

PERCEPT-R gives, for each word a child said, the time it was said in the session recording and the share of
listeners who heard the "r" as correct ($ave in the CHAT file). We cut each word out, run the checker on it,
and compare "was the r right?" with what the listeners said.

Download (free TalkBank account): the transcripts zip and some session audio (.wav) from the media folder.
Each audio file's name matches a .cha file; the same name appears in several study folders, so we pick the
one whose last timestamp matches the recording's length.

    python percept_r.py PERCEPT-R/ audio/ --backend wav2vec --out results.csv

Please cite PERCEPT-R (see its TalkBank page) in anything you publish with these results.
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import re

from align import compare
from backends import make, pad_audio

ITEM = re.compile(r"^\*CHI:\t(.+?) [.?!] \x15?(\d+)_(\d+)\x15?", re.M)
AVE = re.compile(r"\$ave=([\d.]+)")


def find_transcript(tx_dir: str, audio_path: str) -> str | None:
    import soundfile as sf

    name = os.path.splitext(os.path.basename(audio_path))[0]
    dur = sf.info(audio_path).duration
    best = None
    for c in glob.glob(os.path.join(tx_dir, "**", f"{name}.cha"), recursive=True):
        ends = [int(e) for _, _, e in ITEM.findall(open(c, encoding="utf-8").read())]
        if ends:
            gap = abs(max(ends) / 1000 - dur)
            if best is None or gap < best[0]:
                best = (gap, c)
    return best[1] if best and best[0] < 0.5 else None


def items(cha: str):
    """(word, start ms, end ms, share of listeners who heard a correct r) for each word in a session."""
    text = open(cha, encoding="utf-8").read()
    blocks = text.split("\n*CHI:")
    for b in blocks[1:]:
        m = ITEM.match("*CHI:" + b)
        a = AVE.search(b)
        if m and a:
            yield m[1].strip(), int(m[2]), int(m[3]), float(a[1])


def main():
    import librosa

    p = argparse.ArgumentParser()
    p.add_argument("transcripts", help="folder from the PERCEPT-R transcripts zip")
    p.add_argument("audio", help="folder of session .wav files from the media folder")
    p.add_argument("--backend", default="wav2vec", choices=["wav2vec", "gop"])
    p.add_argument("--out", default="percept_r_results.csv")
    a = p.parse_args()

    backend = make(a.backend)
    rows = []
    for wav in sorted(glob.glob(os.path.join(a.audio, "*.wav"))):
        cha = find_transcript(a.transcripts, wav)
        if not cha:
            print(f"{wav}: no matching transcript, skipped")
            continue
        audio, _ = librosa.load(wav, sr=16_000, mono=True)
        for word, start, end, ave in items(cha):
            clip = pad_audio(audio[int(start * 16):int(end * 16)])
            r = compare(word, _expected(word), backend.heard_audio(clip, word), "ɹ")
            if r.target_ok is None:
                continue  # no r in the expected sounds
            rows.append({
                "session": os.path.relpath(cha, a.transcripts), "word": word, "start_ms": start,
                "listeners_correct": ave, "heard": " ".join(r.said),
                "model_says": "correct" if r.target_ok else "distorted",
            })
            print(f"{word:>12}  listeners {ave:.2f}  heard {' '.join(r.said):<16} -> {rows[-1]['model_says']}")

    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    def agree(subset):
        if not subset:
            return "n/a"
        ok = sum((r["listeners_correct"] >= 0.5) == (r["model_says"] == "correct") for r in subset)
        return f"{round(100 * ok / len(subset))}% of {len(subset)}"

    clear_cut = [r for r in rows if r["listeners_correct"] <= 0.2 or r["listeners_correct"] >= 0.8]
    good = [r for r in rows if r["listeners_correct"] >= 0.5]
    bad = [r for r in rows if r["listeners_correct"] < 0.5]
    print()
    print(f"Words:                  {len(rows)}  (listeners: {len(good)} correct, {len(bad)} distorted)")
    print(f"Agrees with listeners:  {agree(rows)}")
    print(f"  clear-cut words only: {agree(clear_cut)}")
    print(f"Distorted r caught:     {sum(r['model_says'] == 'distorted' for r in bad)} of {len(bad)}")
    print(f"Correct r flagged:      {sum(r['model_says'] == 'distorted' for r in good)} of {len(good)}")


_cache: dict[str, list[str]] = {}


def _expected(word: str) -> list[str]:
    from backends import expected_phonemes

    if word not in _cache:
        _cache[word] = expected_phonemes(word)
    return _cache[word]


if __name__ == "__main__":
    main()
