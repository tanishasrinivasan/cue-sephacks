# Catching speech-sound mistakes

A first try at the hardest part of the pivot: telling whether a kid said a word's sounds right, e.g. "rainbow" vs "wainbow".

## How it works

The app already knows which word the kid was asked to say (daily words), so we don't have to understand free speech. We only check one word against what it should sound like:

1. **Expected sounds.** espeak turns the word into its sounds: `rainbow` → `ɹ eɪ n b oʊ`.
2. **Heard sounds.** A phoneme model listens to the recording and writes down the sounds it actually heard, not the word it thinks was meant: `w eɪ n b oʊ`.
3. **Compare.** Line the two up and report what changed: `said w instead of ɹ → gliding (r said as w)`.
4. **Clear try or not.** With a target sound (the one the therapist picked), a try is clear if that sound is right, the way therapists score it. Other sounds can vary, since accents and vowels differ. With no target, at least 80% of the sounds must be right.

**Synthetic test (computer voice, 54 clips, 13 sounds):** 27 words said right and the same 27 said with a typical kid error, covering r, l, s, z, k, g, sh, ch, th (both kinds), f, v and j, at the start, middle and end of words (wainbow, cawwot, wamp, thun, tootie, sue, fumb, ban, dump…).

| Backend                                       | Agrees | Mistakes caught | Good tries flagged |
| --------------------------------------------- | ------ | --------------- | ------------------ |
| `wav2vec` (writes down what it hears)         | 85%    | 26 of 27        | 7 of 27            |
| `gop` (checks each expected sound, see below) | 87%    | 25 of 27        | 5 of 27            |

Most wrongly flagged words had quiet sounds (f, v, th, z) that computer voices blur, so real voices may do better. `gop` misses dropped sounds ("poon" for "spoon") because it assumes every expected sound is there. A second computer voice (Ryan) produced broken clips and was left out. Next is real kids' recordings (PERCEPT-R).

Two things made a big difference: letting the model choose only English sounds (it knows dozens of languages) and padding clips with a quarter second of silence.

**`gop` (goodness of pronunciation):** lines the expected sounds up with the audio, then checks whether another sound fits each stretch better than the expected one. Run it with `--backend gop`.

```
Word:      rainbow
Expected:  ɹ eɪ n b oʊ
Heard:     w eɪ n b oʊ
Accuracy:  80%
Target ɹ: WRONG
  said w instead of ɹ -> gliding (r said as w)
Clear try: no
```

## What we tried from the mentor's list

| Idea                                     | Verdict                                                                                                                                                                                                                                                                                 |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Use existing models before training      | Yes. Two exist that fit, both wired up here.                                                                                                                                                                                                                                            |
| Speech-to-text that doesn't clean up     | That's a **phoneme model**: it outputs sounds, not words. We use `facebook/wav2vec2-lv-60-espeak-cv-ft` (the "wave to back" he meant is wav2vec).                                                                                                                                       |
| Deepgram's confidence score              | Wired up (`--deepgram`) so we can test it, but expect it to be weak: Deepgram is built to get the word right anyway.                                                                                                                                                                    |
| "Perfect waveform" and measure the error | Skipping. Raw sound waves differ hugely between voices (pitch, speed, loudness, especially kids). The phoneme model is the working version of this idea: it compares sounds, not waves.                                                                                                 |
| Phoneme models                           | This is the core of the prototype.                                                                                                                                                                                                                                                      |
| Streaming ASR                            | Not needed yet. For daily words the kid says one word, then we check it, which takes well under a second on a laptop. Live taps in conversation would need streaming later.                                                                                                             |
| Paid API                                 | **Azure pronunciation assessment** gives a score for every sound and, with `NBestPhonemeCount`, which sound it thinks was said instead. Wired up as `--backend azure` (untested: needs a key). Known weakness: it can miss a swapped word that sounds similar, like "they" for "there". |

## Run it

On a laptop with Python 3.10+:

```bash
cd research/pronunciation
pip install -r requirements.txt
python check_word.py rainbow rainbow.wav --target r
```

The first run downloads the model (about 1.2 GB). After that it works offline. Record a short clip of just the word (Voice Memos is fine; m4a, wav and mp3 all work).

Logic tests, no model needed: `python -m unittest`

## Deciding if it's good enough

Don't trust a few tries. Record a test set, have a person mark each one clear or not, and score it:

1. Each of us records 10 words with our target sounds, said right, then the same words said the way a kid with that error would ("wainbow", "thun" for "sun"). Name the files clearly.
2. Fill in a CSV like `recordings.example.csv`.
3. `python evaluate.py recordings.csv --backend wav2vec`

It prints how many real mistakes it caught and how many good tries it wrongly flagged. Both matter: missing mistakes means no help; flagging good tries means a frustrated kid.

**When to train our own model:** if it does fine on our voices but badly on kids' voices, or misses most of a specific error. Then we fine-tune the same model on kids' recordings (a few hours of a rented GPU, not a supercomputer). This is where labeled recordings from therapists become our moat.

Adult voices faking errors is only a start. Before trusting it, we need real kids' recordings, with parents' consent, ideally labeled by a speech therapist.

## Data we can learn from

- **speechocean762**: 5,000 English sentences scored by five experts; half the speakers are children (non-native English). CC BY 4.0. Good for testing on kids' voices.
- **UltraSuite**: audio from child speech therapy sessions, including 28 kids with speech sound disorders. CC BY-NC 4.0: research only, not for a product we sell.
- **SEP-28k** (Apple): 28,000+ clips labeled for stuttering (blocks, prolongations, sound and word repetitions, interjections). For the stuttering version; check its license before using it in the product.

## Next

- Run `evaluate.py` on our own recordings with both backends and compare.
- If wav2vec holds up, move it into the app: an ONNX version of a wav2vec2 espeak model exists, which can run in the browser or on a phone.
- Stuttering is a different detector (repeated sounds, stretched sounds, blocks), better matched to SEP-28k than to this word check.
