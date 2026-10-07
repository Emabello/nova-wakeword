"""Controllo di sicurezza del repository pubblico: blocca chiavi, file audio, local.properties.

  python scripts/check_repo.py            # controlla i file tracciati da git
  python scripts/check_repo.py --staged   # (usato dall'hook pre-push) idem

Esce con codice 1 se trova qualcosa. Lo usano l'hook pre-push e la Action "Controllo sicurezza".
"""
import re
import subprocess
import sys
from pathlib import Path

VIETATI_NOMI = re.compile(r"(^|/)(local\.properties|\.env(\..*)?|.*\.keystore|.*\.jks|.*\.p12|.*\.pem|id_rsa.*|token)$", re.I)
AUDIO = re.compile(r"\.(wav|mp3|flac|ogg|opus|m4a|aac|amr|3gp|webm|pcm|raw)$", re.I)
MAX_BYTES = 5 * 1024 * 1024

SEGRETI = {
    "chiave Google/Gemini": re.compile(r"AIza[0-9A-Za-z_\-]{35}|\bAQ\.[A-Za-z0-9_\-]{30,}"),
    "token Supabase": re.compile(r"\bsbp_[0-9a-f]{40}\b"),
    "token GitHub": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b|github_pat_[A-Za-z0-9_]{40,}"),
    "chiave Anthropic": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    "chiave privata": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "JWT Supabase": re.compile(r"eyJhbGciOi[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}"),
    "token di Nova": re.compile(r"(NOVA_TOKEN|CLAUDE_BRIDGE_TOKEN|GEMINI_API_KEY|SUPABASE_ACCESS_TOKEN)\s*[=:]\s*['\"]?[A-Za-z0-9_\-.]{16,}"),
}


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
    return [p for p in out.decode().split("\0") if p]


def main() -> int:
    problemi = []
    for path in tracked():
        p = Path(path)
        if VIETATI_NOMI.search(path):
            problemi.append(f"{path}: file che non deve stare nel repository")
            continue
        if AUDIO.search(path):
            problemi.append(f"{path}: file audio (le registrazioni restano sul telefono)")
            continue
        if not p.exists():
            continue
        if p.stat().st_size > MAX_BYTES:
            problemi.append(f"{path}: file più grande di 5 MB (i modelli si scaricano dagli artifact)")
            continue
        try:
            testo = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for nome, regex in SEGRETI.items():
            for m in regex.finditer(testo):
                riga = testo.count("\n", 0, m.start()) + 1
                problemi.append(f"{path}:{riga}: sembra un {nome}")
    if problemi:
        print("Controllo sicurezza: push bloccato.\n" + "\n".join(f"  - {x}" for x in problemi))
        return 1
    print("Controllo sicurezza: nessuna chiave, nessun audio, niente local.properties.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
