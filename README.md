# WPS Office 12 in Spanish on Linux

**[Español](README.es.md)** | English

Complete guide to install **WPS Office v12** (12.1.2.25882) on Debian/Ubuntu-based Linux with the interface in **Spanish**, including crash fixes verified by the community.

> WPS Office v12 for Linux only exists as a Chinese build. The international build was abandoned at v11. The language switcher button was **removed in v12**, so the only way to change the language is the manual procedure documented here.

## Result

| Component | Language | Status |
|---|---|---|
| Writer / Spreadsheets / Presentation (editors) | **Spanish (100%)** | Menus, ribbon, dialogs, status bar |
| Spell checker | Spanish (20+ regional variants) | es_ES, es_MX, es_CO, es_AR, ... |
| Launcher / start page | English | Limitation: `prometheus_kso_res.rcc` only exists for en_US |
| Settings center webview | Chinese | Limitation: embedded HTML from the Chinese build |

This matches the maximum achievable translation (~85-90% of total UI) reported by the community. The editors -- where you actually work -- are fully in Spanish.

## Requirements

- Debian/Ubuntu-based distro (tested on Ubuntu 26.04 LTS, KDE Plasma, Wayland)
- ~1.5 GB free disk space
- `wget`, `git`, `sudo`

## Quick install

```bash
git clone https://github.com/andresgarcia0313/wps-office-12-spanish-linux.git
cd wps-office-12-spanish-linux
./install.sh
```

## Manual installation (step by step)

### 1. Download and install WPS Office v12

Use the [Rongronggg9 repack](https://github.com/Rongronggg9/wps-office-repack) (recommended for Wayland/KDE -- includes Fcitx5/XWayland patches and has stable GitHub URLs, unlike the official Chinese CDN whose links expire):

```bash
wget -O /tmp/wps-office-v12.deb \
  "https://github.com/Rongronggg9/wps-office-repack/releases/download/v12.1.2.25882/wps-office_12.1.2.25882.AK.preread.sw%2Bfcitx5xwayland_amd64.deb"
sudo dpkg -i /tmp/wps-office-v12.deb
sudo apt-get install -f -y
```

> If you have WPS v11 installed, this package replaces it (same package name).

### 2. Install the Spanish MUI (translation files)

The [mmvill/WPS_Office_12x_Es](https://github.com/mmvill/WPS_Office_12x_Es) project provides the Qt translation files (`.qm`) specifically for v12:

```bash
git clone --depth 1 https://github.com/mmvill/WPS_Office_12x_Es.git /tmp/WPS_Office_12x_Es
sudo cp -r /tmp/WPS_Office_12x_Es/mui/* /opt/kingsoft/wps-office/office6/mui/
sudo cp -r /tmp/WPS_Office_12x_Es/spellcheck/* /opt/kingsoft/wps-office/office6/dicts/spellcheck/
```

### 3. Install the language registry (critical, undocumented step)

WPS binaries (`libmisc_linux.so`, `libkrt.so`) look for `mui/lang_list/lang_list.json` to register available languages. **Without this file the UI falls back to English** even with correct MUI and config. The file comes from [wachin/wps-office-all-mui-win-language](https://github.com/wachin/wps-office-all-mui-win-language):

```bash
wget -O /tmp/lang_list_community.json \
  "https://github.com/wachin/wps-office-all-mui-win-language/releases/download/v11.1.0.11704/lang_list_community.json"
sudo mkdir -p /opt/kingsoft/wps-office/office6/mui/lang_list/
sudo cp /tmp/lang_list_community.json /opt/kingsoft/wps-office/office6/mui/lang_list/lang_list_community.json
sudo cp /tmp/lang_list_community.json /opt/kingsoft/wps-office/office6/mui/lang_list/lang_list.json
```

### 4. Generate the config file

Launch WPS once so it creates `~/.config/Kingsoft/Office.conf`, then close it:

```bash
timeout 10 wps; pkill -f wpsoffice
```

### 5. Set the language in Office.conf

Edit `~/.config/Kingsoft/Office.conf`:

```ini
[General]
languages=es_ES

[6.0]
common\DefaultLanguage=3082
common\Local\UILanguage=3082
common\do_not_detect_file_association_while_startup=true
```

LCID codes: `3082` = Spanish (Spain), `2058` = Spanish (Mexico), `1033` = English (US).

The `do_not_detect_file_association_while_startup` line prevents WPS from fighting your desktop environment over file associations.

### 6. Crash fixes (strongly recommended)

**Disable `wpscloudsvr`** -- the cloud sync daemon crashes constantly with SIGSEGV in `libqingbangong.so` (widely reported). It is not needed for local use:

```bash
sudo chmod -x /opt/kingsoft/wps-office/office6/wpscloudsvr
rm -rf ~/.local/share/Kingsoft/daemon/
```

**Create the `libtiff.so.5` symlink** -- modern distros only ship `libtiff.so.6`, and WPS needs the old soname for PDF export:

```bash
sudo ln -s /usr/lib/x86_64-linux-gnu/libtiff.so.6 /usr/lib/x86_64-linux-gnu/libtiff.so.5
sudo ldconfig
```

### 7. Done

Open WPS Writer and verify the menus are in Spanish (Inicio, Insertar, Diseño de página, Referencias, Revisar, Vista). Enable the spell checker in **Revisar > Revisión ortográfica** and pick your regional dictionary.

## Bonus: launcher translation (exclusive to this repo)

The WPS home/launcher UI (file list, search bar, quick access, account panel) is NOT covered by any community MUI pack -- its strings live in addon QM files that Kingsoft ships only for `zh_CN`, with **source texts stripped** (hash-only lookup). This repo includes Spanish QMs for those addons, produced by reverse-engineering the format:

```bash
cd launcher-es
sudo ./install-launcher.sh
```

This translates **~3,700 launcher strings**: search bar, file lists, context menus, quick access, sharing dialogs, account panel. Unmatched strings fall back to English (never Chinese).

### How it was made (tools included in `tools/`)

Kingsoft's bundled Qt uses a **modified QM hash**: `elfHash(source + context)` instead of the standard `elfHash(source + comment)`, and strips all source texts from the QM files. The pipeline in `tools/` recovers them:

1. `qm_tool.py parse` -- extracts `(hash -> chinese)` entries from the zh_CN QM
2. `translate_addon.py` -- extracts context names from the QM Contexts block, pulls candidate strings from the addon's `.so` with `strings`, and brute-forces `elfHash(candidate + context)` against the hash table to recover the English sources (~90% recovery rate)
3. Translations applied from `tools/translations_es.json` (3,000+ entry EN->ES translation memory)
4. `qm_tool.py build` -- emits a hash-only QM that WPS loads natively

To translate another addon (or another language), run `translate_addon.py <addon_name>`, fill the generated `*_pending.json`, and build.

## Bonus 2: Settings Center webview translation

The Settings Center (设置中心) is an embedded Vue/CEF webview, separate from the Qt UI. Its HTML loads JS bundles with **Subresource Integrity (SRI)** hashes — editing the JS changes its hash, so CEF *silently* refuses to run it (blank white screen, no error). This is why no community pack translates it.

The fix: edit the JS **and recompute the SRI hash** in the HTML so they match. `settings-es/install-settings.sh` does this automatically (translates, recomputes SHA-384, rewrites `integrity=`, validates with `node --check`):

```bash
cd settings-es
./install-settings.sh
rm -rf ~/.config/cef_user_data/Cache ~/.config/cef_user_data/GPUCache  # clear CEF cache
```

**Diagnosing CEF/SRI failures** (general technique for any blank webview):
```bash
# Compare the declared SRI hash vs the file's real hash - if they differ, CEF blocks it:
printf 'sha384-'; openssl dgst -sha384 -binary entry.js | openssl base64 -A
grep -oP 'integrity="\Ksha384-[^"]*' index.html
```

## Known limitations

- **No language button.** Removed by Kingsoft in v12. Config-file-only.
- **Updates wipe the MUI.** After any WPS update, repeat steps 2, 3, 6 and re-run `launcher-es/install-launcher.sh`.
- **Launcher QMs are build-specific.** Hashes were computed against WPS 12.1.2.25882. On other builds, changed strings simply fall back to English.

## Common mistakes to avoid

| Mistake | Consequence |
|---|---|
| Using [wachin's MUI repo](https://github.com/wachin/wps-office-all-mui-win-language) MUI files for v12 | They target v11; the maintainer explicitly warns against v12. Use mmvill's repo for the MUI, wachin's only for `lang_list_community.json` |
| Skipping `lang_list.json` | UI falls back to English even with correct MUI + Office.conf |
| Downloading the deb from the official Chinese CDN with a saved URL | CDN URLs carry expiring tokens -> 403 Forbidden. Use the repack's GitHub releases or get a fresh link at [linux.wps.cn](https://linux.wps.cn/) |
| Leaving `wpscloudsvr` enabled | Recurring SIGSEGV crashes; can cascade into editor crashes |
| Editing Office.conf while WPS is running | WPS rewrites the file on exit, discarding your changes |

## Credits

- [mmvill/WPS_Office_12x_Es](https://github.com/mmvill/WPS_Office_12x_Es) -- Spanish MUI for v12 (GPL-3.0)
- [wachin/wps-office-all-mui-win-language](https://github.com/wachin/wps-office-all-mui-win-language) -- `lang_list_community.json` and MUI research
- [Rongronggg9/wps-office-repack](https://github.com/Rongronggg9/wps-office-repack) -- v12 repack with Wayland/Fcitx5 patches
- [ArchWiki - WPS Office](https://wiki.archlinux.org/title/WPS_Office) -- crash fixes documentation

## License

GPL-3.0 -- consistent with the upstream MUI project.
