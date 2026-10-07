#!/usr/bin/env bash
# Scarica voci Piper, risposte all'impulso, rumori di fondo e feature negative (una parte).
set -euo pipefail
mkdir -p data voices
HF=https://huggingface.co

for v in it/it_IT/paola/medium/it_IT-paola-medium it/it_IT/riccardo/x_low/it_IT-riccardo-x_low \
         it/it_IT/serena/medium/it_IT-serena-medium it/it_IT/serena/high/it_IT-serena-high \
         en/en_US/libritts_r/medium/en_US-libritts_r-medium; do
  n=$(basename "$v")
  curl -sSfL -o "voices/$n.onnx" "$HF/rhasspy/piper-voices/resolve/main/$v.onnx"
  curl -sSfL -o "voices/$n.onnx.json" "$HF/rhasspy/piper-voices/resolve/main/$v.onnx.json"
done

curl -sSfL -o data/validation_set_features.npy "$HF/datasets/davidscripka/openwakeword_features/resolve/main/validation_set_features.npy"
# ~4 GB delle 2000 ore di feature negative (1,3 milioni di finestre su 5,6): entra nel disco della Action
python trim_npy.py "$HF/datasets/davidscripka/openwakeword_features/resolve/main/openwakeword_features_ACAV100M_2000_hrs_16bit.npy" data/negative_features.npy 1300000

python - <<'PY'
# Risposte all'impulso (MIT) e un'ora di musica/rumore (FMA) per l'augmentation, a 16 kHz
import os, numpy as np, scipy.io.wavfile as w
from datasets import load_dataset, Audio
os.makedirs("data/mit_rirs", exist_ok=True); os.makedirs("data/background", exist_ok=True)
rirs = load_dataset("davidscripka/MIT_environmental_impulse_responses", split="train", streaming=True)
for i, r in enumerate(rirs.cast_column("audio", Audio(sampling_rate=16000))):
    w.write(f"data/mit_rirs/{i}.wav", 16000, (r["audio"]["array"] * 32767).astype(np.int16))
fma = load_dataset("rudraml/fma", name="small", split="train", streaming=True, trust_remote_code=True)
secs = 0
for i, r in enumerate(fma.cast_column("audio", Audio(sampling_rate=16000))):
    a = r["audio"]["array"]
    w.write(f"data/background/fma_{i}.wav", 16000, (a * 32767).astype(np.int16))
    secs += len(a) / 16000
    if secs > 3600: break
print("rirs", len(os.listdir("data/mit_rirs")), "background s", int(secs))
PY
