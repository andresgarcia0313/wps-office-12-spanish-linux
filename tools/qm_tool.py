#!/usr/bin/env python3
"""Parse, match and rebuild Qt QM files for WPS launcher translation.

Kingsoft strips source texts from QM files (hash-only lookup). This tool:
 1. parse: extract (hash -> translation) from a QM
 2. match: recover English sources by hashing candidate strings from the .so
 3. build: create a new QM with the same hashes but new translations
"""
import struct, sys, json, subprocess

MAGIC = bytes.fromhex("3cb86418caef9c95cd211cbf60a1bddd")
T_HASHES, T_MESSAGES, T_CONTEXTS, T_NUMERUS, T_DEPS, T_LANG = 0x42, 0x69, 0x2F, 0x88, 0x96, 0xA7
TAG_END, TAG_TRANSLATION, TAG_SOURCE, TAG_CONTEXT, TAG_COMMENT = 1, 3, 6, 7, 8


def elf_hash(data: bytes) -> int:
    h = 0
    for ch in data:
        h = (h << 4) + ch
        g = h & 0xF0000000
        if g:
            h ^= g >> 24
        h &= ~g & 0xFFFFFFFF
    return h if h else 1


def read_blocks(path):
    raw = open(path, "rb").read()
    assert raw[:16] == MAGIC, "Not a QM file"
    pos, blocks = 16, {}
    while pos < len(raw):
        tag = raw[pos]; length = struct.unpack(">I", raw[pos+1:pos+5])[0]
        blocks[tag] = raw[pos+5:pos+5+length]
        pos += 5 + length
    return blocks


def parse_messages(msg_blob, offset):
    """Read one message at offset; return dict of tags."""
    out, pos = {}, offset
    while pos < len(msg_blob):
        tag = msg_blob[pos]; pos += 1
        if tag == TAG_END:
            break
        if tag == TAG_TRANSLATION:
            ln = struct.unpack(">I", msg_blob[pos:pos+4])[0]; pos += 4
            if ln == 0xFFFFFFFF:
                ln = 0
            out.setdefault("translations", []).append(
                msg_blob[pos:pos+ln].decode("utf-16-be", "replace")); pos += ln
        elif tag in (TAG_SOURCE, TAG_CONTEXT, TAG_COMMENT):
            ln = struct.unpack(">I", msg_blob[pos:pos+4])[0]; pos += 4
            if ln == 0xFFFFFFFF:
                ln = 0
            key = {TAG_SOURCE: "source", TAG_CONTEXT: "context", TAG_COMMENT: "comment"}[tag]
            out[key] = msg_blob[pos:pos+ln].decode("utf-8", "replace"); pos += ln
        else:  # unknown tag: length-prefixed, skip
            ln = struct.unpack(">I", msg_blob[pos:pos+4])[0]; pos += 4 + ln
    return out


def cmd_parse(qm_path, out_json):
    blocks = read_blocks(qm_path)
    hashes, msgs = blocks[T_HASHES], blocks[T_MESSAGES]
    entries = []
    for i in range(0, len(hashes), 8):
        h, off = struct.unpack(">II", hashes[i:i+8])
        m = parse_messages(msgs, off)
        entries.append({"hash": h, "translation": (m.get("translations") or [""])[0],
                        "source": m.get("source", ""), "comment": m.get("comment", "")})
    json.dump(entries, open(out_json, "w"), ensure_ascii=False, indent=1)
    print(f"{len(entries)} entries -> {out_json}")


def cmd_match(qm_json, so_path, out_json):
    entries = json.load(open(qm_json))
    by_hash = {e["hash"]: e for e in entries}
    raw = subprocess.run(["strings", "-a", "-n", "2", so_path],
                         capture_output=True, text=True).stdout.splitlines()
    candidates = set(raw)
    # also try substrings split by common separators
    matched = 0
    for s in candidates:
        h = elf_hash(s.encode("utf-8"))
        if h in by_hash and not by_hash[h].get("english"):
            by_hash[h]["english"] = s
            matched += 1
    json.dump(entries, open(out_json, "w"), ensure_ascii=False, indent=1)
    print(f"matched {matched}/{len(entries)} -> {out_json}")


def cmd_build(map_json, out_qm):
    """Build QM from entries having 'spanish' (fallback: skip)."""
    entries = [e for e in json.load(open(map_json)) if e.get("spanish")]
    entries.sort(key=lambda e: e["hash"])
    msgs, hash_rows = b"", b""
    for e in entries:
        off = len(msgs)
        tr = e["spanish"].encode("utf-16-be")
        msgs += bytes([TAG_TRANSLATION]) + struct.pack(">I", len(tr)) + tr
        msgs += bytes([TAG_END])
        hash_rows += struct.pack(">II", e["hash"], off)
    out = MAGIC
    out += bytes([T_HASHES]) + struct.pack(">I", len(hash_rows)) + hash_rows
    out += bytes([T_MESSAGES]) + struct.pack(">I", len(msgs)) + msgs
    open(out_qm, "wb").write(out)
    print(f"{len(entries)} translations -> {out_qm}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "parse":
        cmd_parse(sys.argv[2], sys.argv[3])
    elif cmd == "match":
        cmd_match(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "build":
        cmd_build(sys.argv[2], sys.argv[3])
