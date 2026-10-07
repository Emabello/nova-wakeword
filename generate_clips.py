"""Genera con Piper le clip sintetiche per addestrare "ehi nova" (al posto di --generate_clips di openWakeWord).

Positivi: le 3 voci italiane di Piper (Paola, Riccardo, Serena) con velocità e intonazione variate, più le
voci del modello inglese multi-voce (LibriTTS-R) che leggono la grafia fonetica "ei nòva" (T2).
Negativi "avversari": frasi che suonano vicine ("ehi Nina", "nove", "nuova"...) e parlato qualunque.

  python generate_clips.py --voices <cartella voci> --out <output_dir/model_name> --n 6000 --n-val 1000
"""
import argparse
import random
import wave
from pathlib import Path

import numpy as np
from piper import PiperVoice
from scipy.signal import resample_poly

IT_VOICES = ["it_IT-paola-medium", "it_IT-riccardo-x_low", "it_IT-serena-medium", "it_IT-serena-high"]
EN_MULTI = "en_US-libritts_r-medium"

POSITIVE_IT = ["ehi nova", "ehi, nova", "ehi Nova!", "ehi nova?", "ehi nova.", "ehi... nova"]
POSITIVE_EN = ["ay nova", "ey nova", "ay, nova", "hey nova"]  # pronuncia vicina all'italiano "ehi nòva"
NEGATIVE_IT = [
    "ehi Nina", "ehi Luna", "ehi Noa", "è nuova", "nove", "nove ore", "ehi nonna", "hai nove anni", "ehi Vanna",
    "la nuova casa", "ehi tu", "ehi ciao", "nova e basta", "Casanova", "ehi novanta", "che ora è", "eh no",
    "ok Google", "ehi Siri", "Alexa", "buongiorno a tutti", "metti un po' di musica", "dove sono le chiavi",
    "ci vediamo alle nove", "una nuova idea", "ehi, non va", "ehi, nuota", "e invece no", "ehi Nicola",
]


def save(path: Path, audio: np.ndarray, rate: int):
    pcm = resample_poly(audio.astype(np.float32), 16000, rate) if rate != 16000 else audio.astype(np.float32)
    pcm = np.clip(pcm, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(pcm.tobytes())


def synth(voice: PiperVoice, text: str, speaker: int | None, rnd: random.Random) -> np.ndarray:
    from piper import SynthesisConfig
    cfg = SynthesisConfig(
        speaker_id=speaker,
        length_scale=rnd.uniform(0.75, 1.35),
        noise_scale=rnd.uniform(0.45, 0.9),
        noise_w_scale=rnd.uniform(0.6, 1.0),
    )
    chunks = [c.audio_int16_array for c in voice.synthesize(text, syn_config=cfg)]
    return np.concatenate(chunks) if chunks else np.zeros(0, np.int16)


def generate(voices_dir: Path, out_dir: Path, n: int, positive: bool, rnd: random.Random):
    out_dir.mkdir(parents=True, exist_ok=True)
    it = [PiperVoice.load(str(voices_dir / f"{v}.onnx")) for v in IT_VOICES if (voices_dir / f"{v}.onnx").exists()]
    en_path = voices_dir / f"{EN_MULTI}.onnx"
    en = PiperVoice.load(str(en_path)) if en_path.exists() else None
    en_speakers = en.config.num_speakers if en else 0
    for i in range(n):
        use_en = en is not None and rnd.random() < (0.5 if positive else 0.3)
        if use_en:
            voice, speaker = en, rnd.randrange(en_speakers)
            text = rnd.choice(POSITIVE_EN if positive else ["hey Nina", "nova", "ay no", "hey now", "a nova", "hey, over"])
        else:
            voice, speaker = rnd.choice(it), None
            text = rnd.choice(POSITIVE_IT if positive else NEGATIVE_IT)
        audio = synth(voice, text, speaker, rnd)
        if audio.size < 1600:
            continue
        save(out_dir / f"{i:06d}.wav", audio, voice.config.sample_rate)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voices", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n", type=int, default=6000)
    ap.add_argument("--n-val", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    for name, n, pos in [("positive_train", a.n, True), ("positive_test", a.n_val, True),
                         ("negative_train", a.n, False), ("negative_test", a.n_val, False)]:
        generate(a.voices, a.out / name, n, pos, rnd)
        print(name, len(list((a.out / name).glob("*.wav"))))


if __name__ == "__main__":
    main()
