# nova-wakeword

Addestramento del modello base **"ehi nova"** per [openWakeWord](https://github.com/dscripka/openWakeWord),
usato dall'assistente vocale personale Nova sul telefono.

Qui ci sono **solo gli script di addestramento**: niente codice dell'app, niente chiavi, niente
registrazioni. Il modello si addestra con voci sintetiche (Piper) e dataset pubblici, e si scarica
dagli artifact della Action; la voce vera dell'utente non lascia mai il telefono (lì c'è un
verificatore personale, addestrato sul posto).

## Come si usa

1. Actions → **Addestra "ehi nova"** → *Run workflow*.
2. A fine corsa, scarica l'artifact `ehi_nova` e importa `ehi_nova.onnx` in Nova → Allenamento.

| File | Cosa fa |
|---|---|
| `fetch_data.sh` | voci Piper (3 italiane + LibriTTS-R inglese), risposte all'impulso MIT, rumori ambientali ESC-50, feature negative |
| `trim_npy.py` | scarica solo ~4 GB dei 17 GB di feature negative (download parziale + intestazione .npy corretta) |
| `generate_clips.py` | clip positive ("ehi nova") e negative con suoni vicini ("ehi Nina", "nove", "nuova"…) |
| `config_ehi_nova.yml` | configurazione per `openwakeword.train` |

## Sicurezza

- **Controllo sicurezza** (Action su ogni push e pull request) e hook `pre-push`
  (`git config core.hooksPath scripts`): bloccano chiavi, file audio, `local.properties`, file sopra 5 MB.
- Scansione dei segreti di GitHub con blocco del push attiva sul repository.

## Licenze

Codice di openWakeWord: Apache 2.0. Le feature negative pre-calcolate e i modelli dell'autore di
openWakeWord sono per uso non commerciale: il modello prodotto è per uso personale.
