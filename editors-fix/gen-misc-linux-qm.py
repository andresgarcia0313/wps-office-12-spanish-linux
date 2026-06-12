#!/usr/bin/env python3
"""Generate es_ES/misc_linux.qm for WPS native Qt dialogs (libmisc_linux.so).

These dialogs (window-mode switch, classic-interface switch, restart alerts)
have NO es_ES QM, so they fall back to the English source strings hardcoded
in the .so. This builds an es_ES QM keyed by Kingsoft's modified Qt hash
elfHash(source + context). Verified: computed hashes match en_US/misc_linux.qm.

Safe by design: a wrong hash simply falls back to English (never breaks).
Install: sudo cp misc_linux.qm /opt/kingsoft/wps-office/office6/mui/es_ES/
"""
import struct, sys

MAGIC = bytes.fromhex("3cb86418caef9c95cd211cbf60a1bddd")
T_HASHES, T_MESSAGES, TAG_END, TAG_TRANSLATION = 0x42, 0x69, 1, 3


def elf_hash(data: bytes) -> int:
    h = 0
    for ch in data:
        h = ((h << 4) + ch) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g: h ^= g >> 24
        h &= (~g) & 0xFFFFFFFF
    return h or 1


# context -> { source_string: spanish }
DIALOGS = {
    "KSwitchAllInOneDlg": {
        "Switch window manage mode": "Cambiar modo de gestión de ventanas",
        "All-in-One Mode": "Modo todo en uno",
        "Support multi-window multi-label depart or group by free":
            "Admite múltiples ventanas y pestañas, separadas o agrupadas libremente",
        "Multi-Module Mode": "Modo multimódulo",
        "Organize file label in different window filter by file type":
            "Organiza las pestañas de archivos en ventanas distintas según el tipo",
        "OK": "Aceptar",
        "Doing this requires to restart WPS, Please close all files in advance in case of data lose.":
            "Esto requiere reiniciar WPS. Cierre todos los archivos antes para evitar pérdida de datos.",
        "Doing this requires to restart WPS, Please close all files in advance in case of data lose":
            "Esto requiere reiniciar WPS. Cierre todos los archivos antes para evitar pérdida de datos",
    },
    "KSwitchToClassicInterfaceDlg": {
        "OK": "Aceptar",
        "Cancel": "Cancelar",
    },
}


def build(out_path):
    entries = []
    for ctx, d in DIALOGS.items():
        for src, es in d.items():
            entries.append((elf_hash((src + ctx).encode("utf-8")), es))
    entries.sort(key=lambda x: x[0])
    msgs, hashes = b"", b""
    for h, tr in entries:
        off = len(msgs)
        t = tr.encode("utf-16-be")
        msgs += bytes([TAG_TRANSLATION]) + struct.pack(">I", len(t)) + t + bytes([TAG_END])
        hashes += struct.pack(">II", h, off)
    out = MAGIC + bytes([T_HASHES]) + struct.pack(">I", len(hashes)) + hashes
    out += bytes([T_MESSAGES]) + struct.pack(">I", len(msgs)) + msgs
    open(out_path, "wb").write(out)
    print(f"{len(entries)} entries -> {out_path}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "misc_linux.qm")
