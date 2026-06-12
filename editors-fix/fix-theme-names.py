#!/usr/bin/env python3
"""Fix mistranslated theme names in wpsoffice.qm (mmvill MUI pack).

The mmvill pack translates the "Clear" skin name as the verb "Borrar"
(erase) instead of the color "Claro" (light). This rebuilds wpsoffice.qm
fixing only the two theme-name hashes, preserving all other translations.

Usage: sudo python3 fix-theme-names.py /opt/kingsoft/wps-office/office6/mui/es_ES/wpsoffice.qm
"""
import struct, sys, os, shutil, datetime

MAGIC = bytes.fromhex("3cb86418caef9c95cd211cbf60a1bddd")
T_HASHES, T_MESSAGES = 0x42, 0x69
TAG_END, TAG_TRANSLATION = 1, 3
# hash -> corrected Spanish theme name
FIXES = {30730894: "Claro (predeterminado)", 159793022: "Oscuro (beta)"}


def log(msg):
    print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}")


def read_blocks(path):
    raw = open(path, "rb").read()
    assert raw[:16] == MAGIC, "not a QM file"
    pos, blocks = 16, {}
    while pos < len(raw):
        tag = raw[pos]; ln = struct.unpack(">I", raw[pos+1:pos+5])[0]
        blocks[tag] = raw[pos+5:pos+5+ln]; pos += 5 + ln
    return blocks


def parse_one(msg, off):
    pos, tr = off, ""
    while pos < len(msg):
        tag = msg[pos]; pos += 1
        if tag == TAG_END: break
        ln = struct.unpack(">I", msg[pos:pos+4])[0]; pos += 4
        if ln == 0xFFFFFFFF: ln = 0
        if tag == TAG_TRANSLATION:
            tr = msg[pos:pos+ln].decode("utf-16-be", "replace")
        pos += ln
    return tr


def main(qm):
    log(f"Leyendo {qm}")
    blocks = read_blocks(qm)
    hashes, msgs = blocks[T_HASHES], blocks[T_MESSAGES]
    entries = []
    for i in range(0, len(hashes), 8):
        h, off = struct.unpack(">II", hashes[i:i+8])
        entries.append([h, parse_one(msgs, off)])
    log(f"{len(entries)} entradas parseadas")

    fixed = 0
    for e in entries:
        if e[0] in FIXES:
            log(f"  {e[0]}: {e[1]!r} -> {FIXES[e[0]]!r}")
            e[1] = FIXES[e[0]]; fixed += 1
    if fixed == 0:
        log("No se encontraron los hashes objetivo (¿ya corregido o build distinta?)")
        return
    log(f"Corregidas: {fixed}")

    out_msgs, out_hashes = b"", b""
    for h, tr in sorted((e for e in entries if e[1]), key=lambda x: x[0]):
        off = len(out_msgs)
        t = tr.encode("utf-16-be")
        out_msgs += bytes([TAG_TRANSLATION]) + struct.pack(">I", len(t)) + t + bytes([TAG_END])
        out_hashes += struct.pack(">II", h, off)
    out = MAGIC + bytes([T_HASHES]) + struct.pack(">I", len(out_hashes)) + out_hashes
    out += bytes([T_MESSAGES]) + struct.pack(">I", len(out_msgs)) + out_msgs

    bak = qm + ".bak-" + datetime.datetime.now().strftime("%s")
    shutil.copy2(qm, bak); log(f"Backup: {bak}")
    open(qm, "wb").write(out); log(f"Escrito {qm} ({len(out)} bytes)")
    log("OK - reinicia WPS para ver 'Claro'/'Oscuro'")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1
         else "/opt/kingsoft/wps-office/office6/mui/es_ES/wpsoffice.qm")
