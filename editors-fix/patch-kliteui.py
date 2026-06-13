#!/usr/bin/env python3
"""Patch es_ES/kliteui.qm: add New-panel headers + icon labels.

The "New" file panel (kcreatefilepanel + libksolite) shows section headers
and product icon labels from kliteui.qm. The mmvill es_ES pack omits them,
so they fall back to English. We add them by hash (reused from en_US/kliteui.qm,
same source+context), preserving all existing mmvill entries.

Usage: sudo python3 patch-kliteui.py /opt/kingsoft/wps-office/office6/mui/es_ES/kliteui.qm
"""
import struct, sys

MAGIC = bytes.fromhex("3cb86418caef9c95cd211cbf60a1bddd")
T_HASHES, T_MESSAGES, TAG_END, TAG_TRANSLATION = 0x42, 0x69, 1, 3

# hash (from en_US/kliteui.qm) -> Spanish
ADD = {
    55442979: "Documento de oficina",   # Office Document
    57246835: "Documento en línea",     # Online Document
    82483123: "Servicios de aplicación",# Application Services
    161834931: "Documento",             # Docs
    223494419: "Presentación",          # Slides
    154616531: "Hoja de cálculo",       # Sheets
    197326771: "Mapa mental",           # MindMap
    178553987: "Diagrama de flujo",     # FlowChart
    109135715: "Página web",            # AirPage
    235630723: "Hoja en línea",         # AirSheet
    239595651: "Tabla de datos",        # DBSheet
}


def read_blocks(path):
    raw = open(path, "rb").read()
    assert raw[:16] == MAGIC
    pos, b = 16, {}
    while pos < len(raw):
        t = raw[pos]; ln = struct.unpack(">I", raw[pos+1:pos+5])[0]
        b[t] = raw[pos+5:pos+5+ln]; pos += 5 + ln
    return b


def parse_tr(msg, off):
    pos = off
    while pos < len(msg):
        tag = msg[pos]; pos += 1
        if tag == TAG_END: break
        ln = struct.unpack(">I", msg[pos:pos+4])[0]; pos += 4
        if ln == 0xFFFFFFFF: ln = 0
        if tag == TAG_TRANSLATION:
            return msg[pos:pos+ln].decode("utf-16-be", "replace")
        pos += ln
    return ""


def main(qm):
    b = read_blocks(qm)
    h, m = b[T_HASHES], b[T_MESSAGES]
    entries = {}
    for i in range(0, len(h), 8):
        hh, off = struct.unpack(">II", h[i:i+8])
        tr = parse_tr(m, off)
        if tr: entries[hh] = tr
    entries.update(ADD)
    items = sorted(entries.items(), key=lambda x: x[0])
    om, oh = b"", b""
    for hh, tr in items:
        off = len(om); t = tr.encode("utf-16-be")
        om += bytes([TAG_TRANSLATION]) + struct.pack(">I", len(t)) + t + bytes([TAG_END])
        oh += struct.pack(">II", hh, off)
    out = MAGIC + bytes([T_HASHES]) + struct.pack(">I", len(oh)) + oh
    out += bytes([T_MESSAGES]) + struct.pack(">I", len(om)) + om
    import shutil, time
    shutil.copy2(qm, f"{qm}.bak-{int(time.time())}")
    open(qm, "wb").write(out)
    print(f"{len(items)} entries ({len(ADD)} added) -> {qm}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/opt/kingsoft/wps-office/office6/mui/es_ES/kliteui.qm")
