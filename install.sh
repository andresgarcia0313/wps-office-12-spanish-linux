#!/bin/bash
# WPS Office 12 in Spanish on Linux - automated installer
# Installs WPS v12 (Rongronggg9 repack), Spanish MUI (mmvill), language
# registry (wachin), and applies community-verified crash fixes.
set -euo pipefail

WPS_DEB_URL="https://github.com/Rongronggg9/wps-office-repack/releases/download/v12.1.2.25882/wps-office_12.1.2.25882.AK.preread.sw%2Bfcitx5xwayland_amd64.deb"
LANG_JSON_URL="https://github.com/wachin/wps-office-all-mui-win-language/releases/download/v11.1.0.11704/lang_list_community.json"
MUI_REPO="https://github.com/mmvill/WPS_Office_12x_Es.git"
WPS_DIR="/opt/kingsoft/wps-office/office6"
CONF="$HOME/.config/Kingsoft/Office.conf"
LCID="${WPS_LCID:-3082}"          # 3082=es_ES, 2058=es_MX
LOCALE="${WPS_LOCALE:-es_ES}"

step() { echo -e "\n==> $1"; }

step "1/7 Downloading WPS Office v12 (~612 MB)"
if ! dpkg -s wps-office 2>/dev/null | grep -q "12.1.2.25882"; then
    wget -O /tmp/wps-office-v12.deb "$WPS_DEB_URL"
    sudo dpkg -i /tmp/wps-office-v12.deb || sudo apt-get install -f -y
else
    echo "WPS v12.1.2.25882 already installed, skipping download."
fi

step "2/7 Installing Spanish MUI and spellcheck dictionaries"
rm -rf /tmp/WPS_Office_12x_Es
git clone --depth 1 "$MUI_REPO" /tmp/WPS_Office_12x_Es
sudo cp -r /tmp/WPS_Office_12x_Es/mui/* "$WPS_DIR/mui/"
sudo cp -r /tmp/WPS_Office_12x_Es/spellcheck/* "$WPS_DIR/dicts/spellcheck/"

step "3/7 Installing language registry (lang_list.json)"
wget -O /tmp/lang_list_community.json "$LANG_JSON_URL"
sudo mkdir -p "$WPS_DIR/mui/lang_list/"
sudo cp /tmp/lang_list_community.json "$WPS_DIR/mui/lang_list/lang_list_community.json"
sudo cp /tmp/lang_list_community.json "$WPS_DIR/mui/lang_list/lang_list.json"

step "4/7 Generating Office.conf (launching WPS briefly)"
if [[ ! -f "$CONF" ]]; then
    timeout 12 wps >/dev/null 2>&1 || true
    pkill -f wpsoffice 2>/dev/null || true
    sleep 2
fi
[[ -f "$CONF" ]] || { echo "ERROR: $CONF was not created. Launch WPS once manually and re-run."; exit 1; }

step "5/7 Setting language to $LOCALE (LCID $LCID)"
pkill -f wpsoffice 2>/dev/null || true; sleep 1
sed -i "s/^languages=.*/languages=$LOCALE/" "$CONF"
grep -q "^languages=" "$CONF" || sed -i "/^\[General\]/a languages=$LOCALE" "$CONF"
sed -i "s/common\\\\DefaultLanguage=.*/common\\\\DefaultLanguage=$LCID/" "$CONF"
sed -i "s/common\\\\Local\\\\UILanguage=.*/common\\\\Local\\\\UILanguage=$LCID/" "$CONF"
grep -q "DefaultLanguage" "$CONF" || sed -i "/^\[6.0\]/a common\\\\DefaultLanguage=$LCID\ncommon\\\\Local\\\\UILanguage=$LCID" "$CONF"
grep -q "do_not_detect_file_association" "$CONF" || \
    sed -i "/^\[6.0\]/a common\\\\do_not_detect_file_association_while_startup=true" "$CONF"

step "6/7 Applying crash fixes"
sudo chmod -x "$WPS_DIR/wpscloudsvr" && echo "  wpscloudsvr disabled (prevents SIGSEGV)"
rm -rf "$HOME/.local/share/Kingsoft/daemon/" 2>/dev/null || true
if [[ ! -e /usr/lib/x86_64-linux-gnu/libtiff.so.5 ]]; then
    sudo ln -s /usr/lib/x86_64-linux-gnu/libtiff.so.6 /usr/lib/x86_64-linux-gnu/libtiff.so.5
    sudo ldconfig
    echo "  libtiff.so.5 symlink created (fixes PDF export)"
fi

step "7/7 Verification"
ls "$WPS_DIR/mui/" | grep -q es_ES && echo "  MUI es_ES: OK"
[[ -f "$WPS_DIR/mui/lang_list/lang_list.json" ]] && echo "  lang_list.json: OK"
grep -q "languages=$LOCALE" "$CONF" && echo "  Office.conf: OK"
[[ ! -x "$WPS_DIR/wpscloudsvr" ]] && echo "  wpscloudsvr: disabled"

echo -e "\nDone. Open WPS Writer and verify the menus are in Spanish."
echo "Enable spellcheck: Revisar > Revision ortografica > pick your dictionary (es_CO, es_ES, ...)."
echo "NOTE: WPS updates wipe the MUI. Re-run this script after updating."
