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
# ~8 GB delle 2000 ore di feature negative (2,6 milioni di finestre su 5,6): entra nel disco della Action dopo la pulizia
python trim_npy.py "$HF/datasets/davidscripka/openwakeword_features/resolve/main/openwakeword_features_ACAV100M_2000_hrs_16bit.npy" data/negative_features.npy 2600000

python - <<'PY'
# Risposte all'impulso (MIT) e rumori di fondo (ESC-50) per l'augmentation, a 16 kHz
import os, numpy as np, scipy.io.wavfile as w
from datasets import load_dataset, Audio
os.makedirs("data/mit_rirs", exist_ok=True); os.makedirs("data/background", exist_ok=True)
rirs = load_dataset("davidscripka/MIT_environmental_impulse_responses", split="train", streaming=True)
for i, r in enumerate(rirs.cast_column("audio", Audio(sampling_rate=16000))):
    w.write(f"data/mit_rirs/{i}.wav", 16000, (r["audio"]["array"] * 32767).astype(np.int16))
# Rumori di fondo: ESC-50 (2.000 clip da 5 s di suoni ambientali; licenza non commerciale)
import io, urllib.request, zipfile
from scipy.signal import resample_poly
z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen("https://github.com/karoldvl/ESC-50/archive/refs/heads/master.zip").read()))
secs = 0
for name in z.namelist():
    if not name.endswith(".wav"):
        continue
    rate, a = w.read(io.BytesIO(z.read(name)))
    a = a.astype(np.float32)
    if a.ndim > 1:
        a = a.mean(axis=1)
    a = resample_poly(a, 16000, rate) if rate != 16000 else a
    w.write(f"data/background/{os.path.basename(name)}", 16000, np.clip(a, -32768, 32767).astype(np.int16))
    secs += len(a) / 16000
print("rirs", len(os.listdir("data/mit_rirs")), "background s", int(secs))
PY
