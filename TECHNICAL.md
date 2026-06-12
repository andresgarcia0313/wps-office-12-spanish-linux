# Technical write-up: translating WPS Office 12 to Spanish

This document explains, layer by layer, how each part of the WPS Office 12 (Linux)
UI was translated, why each layer needs a different technique, and how the
Settings Center webview was fixed after two failed attempts.

WPS Office 12 has **three independent UI layers**, each with its own translation
mechanism:

| Layer | Tech | Mechanism | Difficulty |
|-------|------|-----------|------------|
| 1. Editors (Writer/Sheets/PPT) | Qt | `.qm` MUI files + `Office.conf` | Easy (community packs exist) |
| 2. Launcher / home | Qt (addons) | `.qm` files with stripped sources | Hard (reverse engineering) |
| 3. Settings Center | CEF / Vue webview | minified JS bundles + SRI | Very hard (silent failures) |

---

## Layer 1 — Editors (the easy, documented path)

The editor menus/ribbons use standard Qt translation files (`.qm`). WPS reads the
active locale from `~/.config/Kingsoft/Office.conf` and loads matching `.qm` files
from `/opt/kingsoft/wps-office/office6/mui/<locale>/`.

Steps:
1. Drop `es_ES/` MUI folder (from `mmvill/WPS_Office_12x_Es`) into `mui/`.
2. Set in `Office.conf`: `languages=es_ES`, `common\DefaultLanguage=3082`, `common\Local\UILanguage=3082`.
3. **Critical undocumented step:** create `mui/lang_list/lang_list.json` (from `wachin`). The binaries `libmisc_linux.so`/`libkrt.so` look for it to *register* available locales. Without it, the UI falls back to English even with correct MUI + config.

This is what every community pack does. It does NOT cover layers 2 and 3.

---

## Layer 2 — Launcher (Qt addons with stripped source texts)

The home/launcher UI (file list, search bar, account panel) lives in addon QM files
under `addons/{khyperion,kstartpage,kpromeworkarea,kpromeaccountpanel}/mui/zh_CN/`.
Kingsoft ships these **only in Chinese** and **strips the source texts** from the
QM — it keeps only `(hash -> translation)` pairs, not `(source -> translation)`.

### The QM binary format

A `.qm` file is a tagged binary blob starting with a 16-byte magic. The blocks we
care about:
- `0x42` Hashes: array of `(uint32 elfHash, uint32 messageOffset)`
- `0x69` Messages: per-message tagged records (translation, optional source/context)
- `0x2F` Contexts: hash table + length-prefixed context name pool

### The catch: Kingsoft's modified hash

Standard Qt computes the lookup hash as `elfHash(source + comment)`. Kingsoft uses
`elfHash(source + context)`. Discovered by brute-forcing a known entry:

```
stored hash for source="Share Setting",
  context="KHyperionSpace::FileInfoPanel::KFileInfoPanel_ShareWidget"
= 185765460
elfHash("Share Setting")                 = 2304327      (no)
elfHash("Share Setting" + context)       = 185765460    (MATCH)
```

ELF hash (note: mask `g>>24`, keep 32-bit, never return 0):
```python
def elf_hash(data: bytes) -> int:
    h = 0
    for ch in data:
        h = ((h << 4) + ch) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g: h ^= g >> 24
        h &= (~g) & 0xFFFFFFFF
    return h or 1
```

### Recovering the English sources

Since sources are stripped, we recover them by brute force:
1. Parse the zh_CN QM → list of `(hash, chinese)`.
2. Parse the Contexts block → ~200–300 C++ class names.
3. `strings` the addon's `.so` → ~100k candidate UI strings.
4. For every `candidate × context`, compute `elfHash(candidate+context)` and match
   against the hash table. Pick the most plausible candidate per hash.

Result: ~90% of sources recovered (1521/1633 for khyperion, 2350/2490 for kstartpage).

### Building the Spanish QM

Translate the recovered English → Spanish (translation memory + Gemini for bulk),
then emit a **hash-only** QM (Hashes block + Messages block with just the
translation), keyed by the same hashes. WPS loads it from `mui/es_ES/`.

Tools: `tools/qm_tool.py` (parse/build), `tools/translate_addon.py` (match pipeline),
`tools/translations_es.json` (3000+ entry EN→ES memory).

---

## Layer 3 — Settings Center (CEF webview) — the hard one

The Settings Center (设置中心) is an embedded Vue app rendered by CEF, in
`addons/kweboptioncenter/`. Its strings are hardcoded in minified JS bundles
(`entry/static/js/entry.js`, `static/js/app.js`), not in QM files.

### Failed attempt #1: blind sed

`sed 's/中文/Spanish/g'` on the JS. Two failure modes at once:
- **Substring corruption:** replacing `下载` (download) also hit `下载目录`
  (download folder) → `Descargas目录` (broken half-Chinese string).
- **Hidden in the next failure (SRI).**

### Failed attempt #2: quoted-literal replacement + node --check

Smarter: replace only `"中文"` (with quotes, so quotes are boundaries → no
substring corruption), consistently everywhere (so `title:"X"` and the comparison
`"X"===e.title` stay in sync), and validate with `node --check`.

Still a **blank white screen**. `node --check` passed (syntax valid), so the failure
was at **runtime**, not parse time.

### Root cause: Subresource Integrity (SRI)

The HTML loads its scripts with integrity hashes:
```html
<script src="static/js/entry.js"
        integrity="sha384-GlH9Ipy6isr1NGkdkooFsCIjufJni4AxwND2GQ5GAq05PgigTXsqN6Ptv7XhgImN">
```
Editing the JS changes its SHA-384. CEF/Chromium then **silently refuses to execute
the script** (SRI is designed to fail silent — no console error to the user, the
Vue app just never mounts into `<div id="app">`).

Proof: the original `entry.js` hashed to exactly the value in the HTML.
```bash
$ openssl dgst -sha384 -binary entry.js | openssl base64 -A
GlH9Ipy6isr1NGkdkooFsCIjufJni4AxwND2GQ5GAq05PgigTXsqN6Ptv7XhgImN   # identical
```

### How to diagnose any blank CEF webview

| Method | Command | Detects |
|--------|---------|---------|
| Hash compare | `openssl dgst -sha384 -binary f.js \| openssl base64 -A` vs `integrity=` in HTML | SRI mismatch |
| CEF DevTools | launch with remote debugging, open the console | *"Failed to find a valid digest in the 'integrity' attribute… blocked"* |
| Verbose log | `--log-severity=verbose --log-file=…` → `addons/cef/debug.log` | resource rejection |
| strace | `strace -f -e openat <app> \| grep <webview-dir>` | which files load/fail |

### The working fix

1. Edit the JS — replace only complete quoted literals (`"中文"`), longest-phrase
   first, consistently everywhere.
2. **Recompute** the SHA-384 of the edited file.
3. **Rewrite** the `integrity="sha384-…"` attribute in the HTML to the new hash.
4. Validate with `node --check`.
5. Clear the CEF cache: `rm -rf ~/.config/cef_user_data/Cache ~/.config/cef_user_data/GPUCache`.

`wps_setting_old/static/js/app.js` has **no** SRI attribute → can be edited directly.

Notes:
- The HTML has an RSA-signature comment (`<!--…-->`) and `run.ini` carries a SHA-512,
  but in practice neither blocked the edit — only SRI did. Re-test after each WPS update.
- Strings appear both as visible text (`title:"工作环境"`) and as logic comparisons
  (`"工作环境"===e.title`). Replacing the quoted literal consistently keeps both working.

Tool: `settings-es/install-settings.sh` (translate + recompute SRI + validate).

---

## Maintenance after a WPS update

WPS updates overwrite `/opt/kingsoft/...`, restoring all original (Chinese/English)
files. Re-run, in order:
```bash
./install.sh                         # editors MUI + lang_list + crash fixes
sudo ./launcher-es/install-launcher.sh
./settings-es/install-settings.sh
rm -rf ~/.config/cef_user_data/Cache ~/.config/cef_user_data/GPUCache
```
