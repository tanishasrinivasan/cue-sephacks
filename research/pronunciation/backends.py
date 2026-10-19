"""Ways to turn a recording into the sounds that were said.

Each backend has `heard(path, word) -> list[str]`, a list of IPA phonemes, so they can be
compared on the same recordings (see evaluate.py).

- wav2vec:  Meta's wav2vec2 phoneme model. Free, runs on a laptop, no internet after the first download.
- azure:    Microsoft's pronunciation assessment API. Paid per hour of audio, needs a key.
- deepgram: Not a phoneme backend. Shows how confident Deepgram is about the word (the mentor's
            "use the confidence score" idea), to test whether low confidence catches mistakes.
"""

from __future__ import annotations

import json
import os

# Letters a therapist might type, mapped to the IPA sound the models use.
TARGETS = {
    "r": "ɹ", "s": "s", "z": "z", "l": "l", "k": "k", "g": "ɡ", "f": "f", "v": "v",
    "th": "θ", "dh": "ð", "sh": "ʃ", "ch": "tʃ", "j": "dʒ", "t": "t", "d": "d", "p": "p", "b": "b",
}

WAV2VEC_MODEL = "facebook/wav2vec2-lv-60-espeak-cv-ft"

# The model knows sounds from dozens of languages. We only let it choose English sounds (as espeak writes
# them for American English), plus a few common kid errors that English doesn't use.
ENGLISH_SOUNDS = {
    "p", "b", "t", "d", "k", "ɡ", "f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ", "h", "tʃ", "dʒ", "m", "n", "ŋ",
    "l", "ɹ", "w", "j", "ɾ", "ʔ",
    "i", "iː", "ɪ", "eɪ", "ɛ", "æ", "ɑ", "ɑː", "ɔ", "ɔː", "oʊ", "ʊ", "u", "uː", "ʌ", "ə", "ɐ", "ɚ", "ɜː", "ɝ",
    "aɪ", "aʊ", "ɔɪ", "ɑːɹ", "ɔːɹ", "oːɹ", "ɛɹ", "ɪɹ", "ʊɹ", "əl", "ᵻ",
    "ɬ",  # lateral lisp (s with air out the side)
}


def target_sound(t: str | None) -> str | None:
    if not t:
        return None
    return TARGETS.get(t.lower(), t)


def use_bundled_espeak():
    """Point phonemizer at the espeak bundled by espeakng-loader, so nobody has to install espeak separately."""
    try:
        import espeakng_loader
        from phonemizer.backend.espeak.wrapper import EspeakWrapper

        EspeakWrapper.set_library(espeakng_loader.get_library_path())
        EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
    except ImportError:
        pass


def expected_phonemes(word: str) -> list[str]:
    """The sounds a word should have, from espeak (the same symbol set the wav2vec model was trained on)."""
    from phonemizer import phonemize
    from phonemizer.separator import Separator

    use_bundled_espeak()

    out = phonemize(
        word,
        language="en-us",
        backend="espeak",
        separator=Separator(phone=" ", word=" | ", syllable=""),
        strip=True,
        with_stress=False,
    )
    return [p for p in out.split() if p != "|"]


def load_audio(path: str):
    """Mono float audio at 16 kHz, which both the model and Azure expect."""
    import librosa
    import numpy as np

    audio, _ = librosa.load(path, sr=16_000, mono=True)
    return pad_audio(audio)


def pad_audio(audio):
    """A quarter second of silence on each side: tightly trimmed clips lose their first and last sounds."""
    import numpy as np

    pad = np.zeros(4_000, dtype=audio.dtype)
    return np.concatenate([pad, audio, pad])


class Wav2Vec:
    def __init__(self, model: str = WAV2VEC_MODEL):
        import torch
        from transformers import AutoProcessor, Wav2Vec2ForCTC

        use_bundled_espeak()  # the model's processor checks for espeak when it loads
        self.torch = torch
        self.processor = AutoProcessor.from_pretrained(model)
        self.model = Wav2Vec2ForCTC.from_pretrained(model).eval()
        vocab = self.processor.tokenizer.get_vocab()
        blank = self.processor.tokenizer.pad_token
        keep = [i for tok, i in vocab.items() if tok in ENGLISH_SOUNDS or tok == blank]
        self.mask = torch.full((len(vocab),), float("-inf"))
        self.mask[keep] = 0.0

    def heard(self, path: str, word: str) -> list[str]:
        return self.heard_audio(load_audio(path), word)

    def heard_audio(self, audio, word: str) -> list[str]:
        """Same as heard(), for 16 kHz audio already in memory (padded with pad_audio)."""
        inputs = self.processor(audio, sampling_rate=16_000, return_tensors="pt")
        with self.torch.no_grad():
            logits = self.model(inputs.input_values).logits
        logits = logits + self.mask[: logits.shape[-1]]  # English sounds only
        ids = self.torch.argmax(logits, dim=-1)
        text = self.processor.batch_decode(ids)[0]
        return text.split()


class Wav2VecGOP(Wav2Vec):
    """Goodness of pronunciation: instead of asking the model what it heard, line the expected sounds up
    with the audio, then ask, for each expected sound, whether another sound fits that stretch better.
    Knowing the word makes this much more robust than open transcription."""

    def __init__(self, model: str = WAV2VEC_MODEL, margin: float = 1.0):
        super().__init__(model)
        self.margin = margin  # how much better (in log probability) another sound must fit to count as a swap
        self.vocab = self.processor.tokenizer.get_vocab()
        self.inv = {i: t for t, i in self.vocab.items()}
        self.blank = self.vocab[self.processor.tokenizer.pad_token]

    def heard_audio(self, audio, word: str) -> list[str]:
        torch = self.torch
        expected = expected_phonemes(word)
        targets = [self.vocab[p] for p in expected if p in self.vocab]
        inputs = self.processor(audio, sampling_rate=16_000, return_tensors="pt")
        with torch.no_grad():
            logits = self.model(inputs.input_values).logits[0]
        logp = torch.log_softmax(logits + self.mask[: logits.shape[-1]], dim=-1)
        spans = ctc_align(logp, targets, self.blank)
        said = []
        for tok, frames in zip(targets, spans):
            seg = logp[frames]  # frames this expected sound was aligned to
            mean = seg.mean(0)
            mean[self.blank] = float("-inf")
            best = int(mean.argmax())
            if best != tok and mean[best] - mean[tok] > self.margin:
                said.append(self.inv[best])
            else:
                said.append(self.inv[tok])
        return said


def ctc_align(logp, targets: list[int], blank: int) -> list[list[int]]:
    """Best path of the expected sounds through the model's frame-by-frame probabilities (CTC Viterbi).
    Returns, for each expected sound, the frames it covers (at least one)."""
    import torch

    T = logp.shape[0]
    ext = [blank]
    for t in targets:
        ext += [t, blank]
    S = len(ext)
    neg = float("-inf")
    score = torch.full((T, S), neg)
    back = torch.zeros((T, S), dtype=torch.long)
    score[0, 0] = logp[0, ext[0]]
    if S > 1:
        score[0, 1] = logp[0, ext[1]]
    for t in range(1, T):
        for s in range(S):
            cands = [(score[t - 1, s], s)]
            if s >= 1:
                cands.append((score[t - 1, s - 1], s - 1))
            if s >= 2 and ext[s] != blank and ext[s] != ext[s - 2]:
                cands.append((score[t - 1, s - 2], s - 2))
            v, prev = max(cands, key=lambda c: c[0])
            score[t, s] = v + logp[t, ext[s]]
            back[t, s] = prev
    s = S - 1 if S == 1 or score[T - 1, S - 1] >= score[T - 1, S - 2] else S - 2
    path = [0] * T
    for t in range(T - 1, -1, -1):
        path[t] = s
        s = int(back[t, s])
    spans: list[list[int]] = [[] for _ in targets]
    for t, s in enumerate(path):
        if s % 2 == 1:
            spans[(s - 1) // 2].append(t)
    # Every expected sound needs at least one frame; borrow the nearest one if the path skipped it.
    for k in range(len(spans)):
        if not spans[k]:
            near = [t for t, s in enumerate(path) if s == 2 * k + 1 or s == 2 * k or s == 2 * k + 2]
            spans[k] = near[:1] or [min(T - 1, k)]
    return spans


class Azure:
    """Needs AZURE_SPEECH_KEY and AZURE_SPEECH_REGION. Not tested in our environment yet."""

    def __init__(self):
        import azure.cognitiveservices.speech as speechsdk

        self.sdk = speechsdk
        self.config = speechsdk.SpeechConfig(
            subscription=os.environ["AZURE_SPEECH_KEY"], region=os.environ["AZURE_SPEECH_REGION"]
        )
        self.last = None  # the raw result, for its own scores

    def heard(self, path: str, word: str) -> list[str]:
        sdk = self.sdk
        pa = sdk.PronunciationAssessmentConfig(
            reference_text=word,
            grading_system=sdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=sdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True,
        )
        pa.phoneme_alphabet = "IPA"
        pa.nbest_phoneme_count = 5  # what was most likely said, for each expected sound
        audio = sdk.audio.AudioConfig(filename=path)
        rec = sdk.SpeechRecognizer(speech_config=self.config, language="en-US", audio_config=audio)
        pa.apply_to(rec)
        result = rec.recognize_once()
        data = json.loads(result.properties.get(sdk.PropertyId.SpeechServiceResponse_JsonResult) or "{}")
        self.last = data
        said: list[str] = []
        for w in (data.get("NBest") or [{}])[0].get("Words", []):
            for ph in w.get("Phonemes", []):
                best = ph.get("PronunciationAssessment", {}).get("NBestPhonemes") or []
                said.append(best[0]["Phoneme"] if best else ph.get("Phoneme", ""))
        return said


def deepgram_confidence(path: str, word: str) -> float | None:
    """Deepgram's confidence (0-1) for the word, or None if it didn't hear it. Needs DEEPGRAM_API_KEY."""
    import requests

    with open(path, "rb") as f:
        r = requests.post(
            "https://api.deepgram.com/v1/listen",
            params={"model": "nova-3", "language": "en-US", "keyterm": word},
            headers={"Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}", "Content-Type": "audio/wav"},
            data=f.read(),
            timeout=30,
        )
    r.raise_for_status()
    words = r.json()["results"]["channels"][0]["alternatives"][0].get("words", [])
    scores = [w["confidence"] for w in words if w["word"].lower().strip(".,!?") == word.lower()]
    return max(scores) if scores else None


def make(name: str):
    if name == "wav2vec":
        return Wav2Vec()
    if name == "gop":
        return Wav2VecGOP()
    if name == "azure":
        return Azure()
    raise SystemExit(f"Unknown backend {name!r}: use wav2vec or azure")
