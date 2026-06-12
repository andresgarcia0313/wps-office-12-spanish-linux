#!/usr/bin/env python3
"""Pipeline: translate a WPS addon's zh_CN QM to Spanish.

Usage: translate_addon.py <addon_name> [<qm_name>]
Steps: parse zh QM -> extract contexts -> match .so strings (elfHash(src+ctx))
       -> apply translation memory -> dump pending -> (after filling) build QM
"""
import json, re, struct, subprocess, sys, os
from qm_tool import read_blocks, parse_messages, elf_hash, T_HASHES, T_MESSAGES, T_CONTEXTS

ADDONS = "/opt/kingsoft/wps-office/office6/addons"
MEMORY = "/home/andres/tmp-translate/translations_es.json"


def elf_step(h, data):
    for ch in data:
        h = ((h << 4) + ch) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g:
            h ^= g >> 24
        h &= (~g) & 0xFFFFFFFF
    return h


def plausible(s):
    if not s or len(s) < 2:
        return False
    if not re.match(r'^[A-Za-z0-9"%(<\[{\'$]', s):
        return False
    if re.search(r'[\x00-\x08\x0b-\x1f]', s):
        return False
    if re.match(r'^(N\d|Z[NZ]|St\d|_Z)', s):  # mangled C++ symbols
        return False
    ok = sum(1 for c in s if c.isalnum() or c in ' .,;:!?%()[]{}<>/\\\'"-_=+&*#@\n\t')
    return ok / len(s) > 0.9


def parse_contexts(blob):
    size = struct.unpack(">H", blob[:2])[0]
    pos, out = 2 + 2 * size, []
    while pos < len(blob):
        ln = blob[pos]; pos += 1
        if ln == 0:
            continue
        out.append(blob[pos:pos+ln].decode('utf-8', 'replace')); pos += ln
    return sorted(set(out))


def main(addon, qm_name=None):
    mui = f"{ADDONS}/{addon}/mui/zh_CN"
    qm_path = f"{mui}/{qm_name}" if qm_name else None
    if not qm_path:
        qms = [f for f in os.listdir(mui) if f.endswith('.qm')]
        qm_path = f"{mui}/{qms[0]}"
    so_candidates = [f"{ADDONS}/{addon}/lib{addon}.so"] + [
        f"{ADDONS}/{addon}/{f}" for f in os.listdir(f"{ADDONS}/{addon}") if f.endswith('.so')]
    so_path = next((p for p in so_candidates if os.path.exists(p)), None)
    print(f"QM: {qm_path}\nSO: {so_path}")

    blocks = read_blocks(qm_path)
    hashes, msgs = blocks[T_HASHES], blocks[T_MESSAGES]
    entries = []
    for i in range(0, len(hashes), 8):
        h, off = struct.unpack(">II", hashes[i:i+8])
        m = parse_messages(msgs, off)
        entries.append({"hash": h, "translation": (m.get("translations") or [""])[0],
                        "source": m.get("source", "")})
    contexts = parse_contexts(blocks[T_CONTEXTS]) if T_CONTEXTS in blocks else []
    print(f"{len(entries)} entries, {len(contexts)} contexts")

    target = {}
    for e in entries:
        target.setdefault(e['hash'], []).append(e)

    raw = subprocess.run(['strings', '-a', '-n', '2', so_path],
                         capture_output=True, text=True).stdout.splitlines()
    candidates = sorted(set(s for s in raw if len(s) < 400))
    allm = {}
    ctx_b = [(c.encode(), c) for c in contexts]
    for src in candidates:
        st = elf_step(0, src.encode())
        for cb, ctx in ctx_b:
            h = elf_step(st, cb) or 1
            if h in target:
                allm.setdefault(h, set()).add(src)

    memory = json.load(open(MEMORY)) if os.path.exists(MEMORY) else {}
    matched = pending = 0
    for e in entries:
        cands = allm.get(e['hash'], set())
        if e['source']:
            e['english'] = e['source']
        elif cands:
            plaus = [c for c in cands if plausible(c)]
            e['english'] = max(plaus or list(cands), key=len)
        else:
            continue
        matched += 1
        if memory.get(e['english']):
            e['spanish'] = memory[e['english']]
        elif plausible(e['english']):
            pending += 1

    pend = sorted({e['english']: e['translation'] for e in entries
                   if e.get('english') and not e.get('spanish')
                   and plausible(e['english'])}.items())
    print(f"Matched: {matched}/{len(entries)} | from memory: "
          f"{sum(1 for e in entries if e.get('spanish'))} | pending: {len(pend)}")
    json.dump(entries, open(f'{addon}_work.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(dict(pend), open(f'{addon}_pending.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
