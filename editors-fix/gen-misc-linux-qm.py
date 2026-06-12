#!/usr/bin/env python3
"""Generate es_ES/misc_linux.qm for WPS native Qt dialogs (libmisc_linux.so).

Native dialogs (window-mode switch, classic-interface switch, restart/print
alerts) have NO es_ES QM, so they fall back to English/Chinese source strings
hardcoded in the .so. Qt looks up translations by hash = elfHash(source+context),
so we only need the HASH, not the source string. We reuse the exact hashes from
en_US/misc_linux.qm (same .so, same hashes) with Spanish translations.

Safe by design: a hash with no runtime match simply isn't used (English/Chinese
fallback), never breaks anything.

Build:   python3 gen-misc-linux-qm.py misc_linux.qm
Install: sudo cp misc_linux.qm /opt/kingsoft/wps-office/office6/mui/es_ES/
"""
import struct, sys, json, os

MAGIC = bytes.fromhex("3cb86418caef9c95cd211cbf60a1bddd")
T_HASHES, T_MESSAGES, TAG_END, TAG_TRANSLATION = 0x42, 0x69, 1, 3

MAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "misc_linux_es_map.json")


def build(out_path):
    es = {int(k): v for k, v in json.load(open(MAP, encoding="utf-8")).items()}
    entries = sorted(es.items(), key=lambda x: x[0])
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
