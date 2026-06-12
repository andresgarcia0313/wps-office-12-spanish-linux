#!/bin/bash
# Translates the WPS Office 12 Settings Center (设置中心) CEF webview to Spanish.
#
# WHY THIS IS TRICKY: the settings page is an embedded Vue/CEF app whose HTML
# loads its JS bundles with Subresource Integrity (SRI) hashes:
#   <script src="entry.js" integrity="sha384-...">
# Editing the JS changes its hash, so CEF SILENTLY refuses to run it (no error,
# blank white screen). The fix is to edit the JS AND recompute the SRI hash in
# the HTML so they match again. This is why no community MUI pack covers it.
#
# This script: translates each JS bundle, recomputes its SHA-384, and rewrites
# the matching integrity="..." attribute. Validates JS with `node --check`.
# Run from settings-es/: sudo not needed (uses sudo internally per file).
set -euo pipefail

ADDON="/opt/kingsoft/wps-office/office6/addons/kweboptioncenter"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v node >/dev/null || { echo "ERROR: node required for validation"; exit 1; }
command -v openssl >/dev/null || { echo "ERROR: openssl required for SRI hashes"; exit 1; }

sri_of() { printf 'sha384-'; openssl dgst -sha384 -binary "$1" | openssl base64 -A; }

# JS bundle -> HTML that declares its SRI (empty = no SRI, edit freely)
translate_bundle() {
    local js="$1" html="$2"
    [[ -f "$js" ]] || { echo "SKIP (missing): $js"; return; }
    [[ -f "$js.bak" ]] || sudo cp "$js" "$js.bak"   # one-time backup

    local oldhash="" tmp="/tmp/wps_settings_$$.js"
    [[ -n "$html" && -f "$html" ]] && oldhash="$(sri_of "$js.bak")"

    cp "$js.bak" "$tmp"
    python3 "$DIR/safe_translate_settings.py" "$tmp" >/dev/null
    if ! node --check "$tmp" 2>/dev/null; then
        echo "ABORT (JS broke): $js"; rm -f "$tmp"; return
    fi
    sudo cp "$tmp" "$js"
    if [[ -n "$oldhash" ]]; then
        local newhash; newhash="$(sri_of "$js")"
        sudo sed -i "s|$oldhash|$newhash|g" "$html"
        echo "OK + SRI: $(basename "$js")"
    else
        echo "OK: $(basename "$js")"
    fi
    rm -f "$tmp"
}

translate_bundle "$ADDON/entry/static/js/entry.js"          "$ADDON/entry/index.html"
translate_bundle "$ADDON/static/js/app.js"                  "$ADDON/index.html"
translate_bundle "$ADDON/wps_setting_old/static/js/app.js"  ""

# HTML <title>
sudo sed -i 's/<title>设置中心<\/title>/<title>Centro de configuración<\/title>/g' "$ADDON/entry/index.html" 2>/dev/null || true

echo
echo "Done. Clear the CEF cache and restart WPS:"
echo "  rm -rf ~/.config/cef_user_data/Cache ~/.config/cef_user_data/GPUCache"
echo "NOTE: WPS updates restore the original bundles - re-run this script after updating."
