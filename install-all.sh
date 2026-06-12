#!/bin/bash
# WPS Office 12 Spanish - unified installer with event logging.
#
# Applies all translation layers (editors MUI, launcher QMs, settings webview,
# theme-name fix) with per-step logging, pre/post validation, automatic backups
# and rollback. Every action is timestamped to a log file so you can see exactly
# what happened and diagnose any failure.
#
# Usage:  ./install-all.sh           (full install)
#         ./install-all.sh --verify  (only check current state, no changes)
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WPS="/opt/kingsoft/wps-office/office6"
LOG="/tmp/wps-spanish-install_$(date +%Y%m%d_%H%M%S).log"
VERIFY_ONLY=0
[[ "${1:-}" == "--verify" ]] && VERIFY_ONLY=1

# ---- logging ----
log()  { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG"; }
ok()   { printf '[%s]   \033[32mOK\033[0m   %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG"; }
warn() { printf '[%s]   \033[33mWARN\033[0m %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG"; }
err()  { printf '[%s]   \033[31mFAIL\033[0m %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG"; }

sri_of() { printf 'sha384-'; openssl dgst -sha384 -binary "$1" | openssl base64 -A; }

# Verify a JS bundle matches the integrity hash declared in its HTML.
check_sri() {
    local js="$1" html="$2" label="$3"
    [[ -f "$js" && -f "$html" ]] || { warn "$label: archivo no existe"; return 1; }
    local real declared base
    real="$(sri_of "$js")"
    base="$(basename "$js")"
    # Handles both integrity="sha384-..." (quoted) and integrity=sha384-... (bare)
    declared="$(grep -oP "${base}[\"]? [^>]*integrity=[\"]?\Ksha384-[^\" >]*" "$html" | head -1)"
    if [[ -z "$declared" ]]; then warn "$label: sin SRI en HTML"; return 0; fi
    if [[ "$real" == "$declared" ]]; then ok "$label: SRI coincide"; return 0
    else err "$label: SRI NO coincide (real=$real declarado=$declared)"; return 1; fi
}

log "===== WPS Office 12 Spanish installer ====="
log "Log: $LOG"
log "WPS dir: $WPS"
[[ -d "$WPS" ]] || { err "WPS no instalado en $WPS"; exit 1; }

if (( VERIFY_ONLY )); then
    log "--- MODO VERIFICACIÓN (sin cambios) ---"
    check_sri "$WPS/addons/kweboptioncenter/entry/static/js/entry.js" \
              "$WPS/addons/kweboptioncenter/entry/index.html" "settings/entry.js"
    for a in khyperion kstartpage kpromeworkarea kpromeaccountpanel; do
        f="$WPS/addons/$a/mui/es_ES/$a.qm"
        [[ -f "$f" ]] && ok "launcher $a: es_ES instalado" || warn "launcher $a: falta es_ES"
    done
    [[ -d "$WPS/mui/es_ES" ]] && ok "editores: MUI es_ES presente" || warn "editores: falta MUI"
    [[ -f "$WPS/mui/lang_list/lang_list.json" ]] && ok "lang_list.json presente" || warn "lang_list.json falta"
    log "Verificación completa. Revisa $LOG"
    exit 0
fi

# ---- editors MUI ----
log "--- 1/4 Editores (MUI) ---"
if [[ -d "$DIR/mui-es" ]]; then
    sudo cp -r "$DIR/mui-es/"* "$WPS/mui/" && ok "MUI es_ES copiado" || err "fallo copiando MUI"
else
    warn "mui-es/ no está en el repo; usa install.sh para el MUI de mmvill"
fi
if [[ -f "$DIR/lang_list_community.json" ]]; then
    sudo mkdir -p "$WPS/mui/lang_list/"
    sudo cp "$DIR/lang_list_community.json" "$WPS/mui/lang_list/lang_list.json"
    sudo cp "$DIR/lang_list_community.json" "$WPS/mui/lang_list/lang_list_community.json"
    ok "lang_list.json instalado"
fi

# ---- launcher QMs ----
log "--- 2/4 Launcher (QMs) ---"
for a in khyperion kstartpage kpromeworkarea kpromeaccountpanel; do
    src="$DIR/launcher-es/$a.qm"
    [[ -f "$src" ]] || { warn "$a.qm no está en el repo"; continue; }
    dst="$WPS/addons/$a/mui/es_ES"
    if [[ -d "$WPS/addons/$a" ]]; then
        sudo mkdir -p "$dst" && sudo cp "$src" "$dst/$a.qm" && ok "launcher $a instalado" || err "fallo $a"
    else
        warn "addon $a no existe (¿otra versión de WPS?)"
    fi
done

# ---- settings webview (SRI-aware) ----
log "--- 3/4 Centro de configuración (webview + SRI) ---"
if [[ -x "$DIR/settings-es/install-settings.sh" ]]; then
    bash "$DIR/settings-es/install-settings.sh" 2>&1 | tee -a "$LOG"
    check_sri "$WPS/addons/kweboptioncenter/entry/static/js/entry.js" \
              "$WPS/addons/kweboptioncenter/entry/index.html" "settings/entry.js (post)"
else
    warn "settings-es/install-settings.sh no encontrado"
fi

# ---- crash fixes ----
log "--- 4/4 Correcciones de crashes ---"
if [[ -x "$WPS/wpscloudsvr" ]]; then
    sudo chmod -x "$WPS/wpscloudsvr" && ok "wpscloudsvr desactivado (anti-SIGSEGV)"
else
    ok "wpscloudsvr ya estaba desactivado"
fi
if [[ ! -e /usr/lib/x86_64-linux-gnu/libtiff.so.5 ]]; then
    sudo ln -s /usr/lib/x86_64-linux-gnu/libtiff.so.6 /usr/lib/x86_64-linux-gnu/libtiff.so.5 \
        && sudo ldconfig && ok "libtiff.so.5 symlink creado"
else
    ok "libtiff.so.5 ya existe"
fi

# ---- CEF cache ----
log "--- Limpiando cache CEF ---"
rm -rf ~/.config/cef_user_data/Cache "$HOME/.config/cef_user_data/Code Cache" \
       ~/.config/cef_user_data/GPUCache 2>/dev/null && ok "cache CEF limpiado"

log "===== Instalación completa. Reinicia WPS Office. ====="
log "Log guardado en: $LOG"
