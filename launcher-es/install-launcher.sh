#!/bin/bash
# Installs the Spanish launcher translation QMs for WPS Office 12.
# These translate the home/launcher UI (khyperion, kstartpage, kpromeworkarea,
# kpromeaccountpanel) which no community MUI pack covers.
# Run from the launcher-es/ directory: sudo ./install-launcher.sh
set -euo pipefail

ADDONS="/opt/kingsoft/wps-office/office6/addons"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

declare -A QMS=(
    [khyperion]=khyperion.qm
    [kstartpage]=kstartpage.qm
    [kpromeworkarea]=kpromeworkarea.qm
    [kpromeaccountpanel]=kpromeaccountpanel.qm
)

for addon in "${!QMS[@]}"; do
    qm="${QMS[$addon]}"
    if [[ ! -d "$ADDONS/$addon" ]]; then
        echo "SKIP: addon $addon not found (different WPS version?)"
        continue
    fi
    sudo mkdir -p "$ADDONS/$addon/mui/es_ES/"
    sudo cp "$DIR/$qm" "$ADDONS/$addon/mui/es_ES/$qm"
    echo "OK: $addon/mui/es_ES/$qm"
done

echo
echo "Done. Restart WPS Office to load the launcher translation."
echo "NOTE: built for WPS 12.1.2.25882. Other builds may have different"
echo "string hashes - untranslated strings fall back to English (never Chinese)."
