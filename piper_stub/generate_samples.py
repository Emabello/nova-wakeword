"""Segnaposto: openwakeword/train.py importa sempre `generate_samples` di piper-sample-generator,
ma qui le clip le genera generate_clips.py (voci italiane). Questa funzione non viene mai chiamata."""


def generate_samples(*args, **kwargs):
    raise RuntimeError("Le clip si generano con generate_clips.py, non con --generate_clips")
