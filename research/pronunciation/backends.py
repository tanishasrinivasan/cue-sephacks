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

    audio, _ = librosa.load(path, sr=16_000, mono=True)
    return audio


class Wav2Vec:
    def __init__(self, model: str = WAV2VEC_MODEL):
        import torch
        from transformers import AutoProcessor, Wav2Vec2ForCTC

        use_bundled_espeak()  # the model's processor checks for espeak when it loads
        self.torch = torch
        self.processor = AutoProcessor.from_pretrained(model)
        self.model = Wav2Vec2ForCTC.from_pretrained(model).eval()

    def heard(self, path: str, word: str) -> list[str]:
        audio = load_audio(path)
        inputs = self.processor(audio, sampling_rate=16_000, return_tensors="pt")
        with self.torch.no_grad():
            logits = self.model(inputs.input_values).logits
        ids = self.torch.argmax(logits, dim=-1)
        text = self.processor.batch_decode(ids)[0]
        return text.split()


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
    if name == "azure":
        return Azure()
    raise SystemExit(f"Unknown backend {name!r}: use wav2vec or azure")
