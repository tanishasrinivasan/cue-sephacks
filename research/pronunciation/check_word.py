"""Check one recording of one word.

    python check_word.py rainbow take1.wav --target r
    python check_word.py rainbow take1.wav --target r --backend azure
    python check_word.py rainbow take1.wav --deepgram
"""

import argparse

from align import compare
from backends import deepgram_confidence, expected_phonemes, make, target_sound


def main():
    p = argparse.ArgumentParser(description="Did the child say the word's sounds right?")
    p.add_argument("word")
    p.add_argument("audio", help="a short recording of just that word (wav, m4a, mp3)")
    p.add_argument("--target", help="the sound being practiced, e.g. r, s, th, sh, l")
    p.add_argument("--backend", default="wav2vec", choices=["wav2vec", "azure"])
    p.add_argument("--deepgram", action="store_true", help="also print Deepgram's confidence for the word")
    a = p.parse_args()

    backend = make(a.backend)
    result = compare(a.word, expected_phonemes(a.word), backend.heard(a.audio, a.word), target_sound(a.target))
    print(result.explain())
    if a.deepgram:
        c = deepgram_confidence(a.audio, a.word)
        print(f"Deepgram confidence: {'did not hear the word' if c is None else round(c, 3)}")


if __name__ == "__main__":
    main()
