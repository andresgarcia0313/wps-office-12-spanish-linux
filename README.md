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

## Known limitations

- **Launcher / start page stays in English.** The es_ES MUI lacks `prometheus_kso_res.rcc` (Prometheus UI resources); only en_US ships it. Compiled Qt resource -- not community-translatable.
- **Settings center webview stays in Chinese.** It is embedded HTML inside the Chinese build rendered by CEF; locale `.pak` files do not affect it.
- **No language button.** Removed by Kingsoft in v12. Config-file-only.
- **Updates wipe the MUI.** After any WPS update, repeat steps 2, 3 and 6.

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
