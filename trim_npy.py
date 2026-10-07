"""Scarica solo l'inizio del file di feature negative di openWakeWord (17 GB) e lo rende un .npy valido.

  python trim_npy.py <url> <output.npy> <righe>
"""
import ast
import sys
import urllib.request

url, out, rows = sys.argv[1], sys.argv[2], int(sys.argv[3])
head = urllib.request.urlopen(urllib.request.Request(url, headers={"Range": "bytes=0-4095"})).read()
assert head[:6] == b"\x93NUMPY", "non è un file .npy"
major = head[6]
hlen = int.from_bytes(head[8:10], "little") if major == 1 else int.from_bytes(head[8:12], "little")
start = (10 if major == 1 else 12) + hlen
meta = ast.literal_eval(head[(10 if major == 1 else 12):start].decode("latin1"))
shape = meta["shape"]
row_bytes = 2 if "2" in meta["descr"] else 4
for d in shape[1:]:
    row_bytes *= d
rows = min(rows, shape[0])
meta["shape"] = (rows,) + tuple(shape[1:])
text = repr(meta).encode("latin1")
pad = 64 - (10 + len(text) + 1) % 64
header = b"\x93NUMPY\x01\x00" + (len(text) + pad + 1).to_bytes(2, "little") + text + b" " * pad + b"\n"
need = rows * row_bytes
req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{start + need - 1}"})
with urllib.request.urlopen(req) as r, open(out, "wb") as f:
    f.write(header)
    got = 0
    while chunk := r.read(1 << 22):
        f.write(chunk); got += len(chunk)
assert got == need, f"scaricati {got} byte su {need}"
print(f"{out}: {meta['shape']} {meta['descr']}")
