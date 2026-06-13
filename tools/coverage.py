#!/usr/bin/env python3
"""Autonomous translation-coverage report for WPS Office 12 (Linux).

Compares every en_US QM against its es_ES counterpart by hash set (the QMs
are hash-only: elfHash(source+context)). A hash present in en_US but missing
or empty in es_ES = an untranslated Qt string. Also flags addons with no
es_ES dir at all, and (optionally) scans CEF webview JS bundles for hardcoded
CJK literals.

No GUI, no PyQt, pure stdlib. Run headless/nightly.

Usage:
  python3 coverage.py                 # full report
  python3 coverage.py --top 15        # worst 15 QMs
  python3 coverage.py --cef           # also scan webview JS for Chinese
  python3 coverage.py --qm NAME       # detail one QM (missing hashes)
"""
import struct, sys, os, glob, re

WPS = "/opt/kingsoft/wps-office/office6"
MAGIC = bytes.fromhex("3cb86418caef9c95cd211cbf60a1bddd")
T_HASHES, T_MESSAGES, TAG_END, TAG_TRANSLATION = 0x42, 0x69, 1, 3
CJK = re.compile(r"[\u4e00-\u9fff]")


def read_blocks(path):
    raw = open(path, "rb").read()
    if raw[:16] != MAGIC:
        return {}
    pos, b = 16, {}
    while pos < len(raw):
        t = raw[pos]; ln = struct.unpack(">I", raw[pos+1:pos+5])[0]
        b[t] = raw[pos+5:pos+5+ln]; pos += 5 + ln
    return b


def qm_hashes(path):
    """Return set of hashes that have a NON-EMPTY translation."""
    b = read_blocks(path)
    if T_HASHES not in b:
        return set()
    h, m = b[T_HASHES], b.get(T_MESSAGES, b"")
    out = set()
    for i in range(0, len(h), 8):
        hh, off = struct.unpack(">II", h[i:i+8])
        # check translation non-empty
        pos = off; tr_len = -1
        while pos < len(m):
            tag = m[pos]; pos += 1
            if tag == TAG_END:
                break
            ln = struct.unpack(">I", m[pos:pos+4])[0]; pos += 4
            if ln == 0xFFFFFFFF:
                ln = 0
            if tag == TAG_TRANSLATION:
                tr_len = ln
            pos += ln
        if tr_len != 0:
            out.add(hh)
    return out


def find_qm_pairs():
    """Map qm relative name -> (en_path, es_path or None)."""
    pairs = {}
    for en in glob.glob(f"{WPS}/mui/en_US/*.qm") + glob.glob(f"{WPS}/addons/*/mui/en_US/*.qm"):
        rel = en.replace("/en_US/", "/es_ES/")
        name = en.replace(WPS + "/", "")
        pairs[name] = (en, rel if os.path.exists(rel) else None)
    return pairs


def coverage(top=None):
    pairs = find_qm_pairs()
    rows, tot_en, tot_es, no_es = [], 0, 0, 0
    for name, (en, es) in sorted(pairs.items()):
        en_h = qm_hashes(en)
        es_h = qm_hashes(es) if es else set()
        missing = len(en_h - es_h)
        tot_en += len(en_h); tot_es += len(en_h) - missing
        if es is None:
            no_es += 1
        rows.append((name, len(en_h), missing, es is None))
    rows.sort(key=lambda r: -r[2])
    print(f"== WPS Office 12 - Cobertura de traducción (Qt QM) ==")
    print(f"Total strings (en_US): {tot_en}")
    print(f"Traducidos (es_ES):    {tot_es}  ({100*tot_es//max(tot_en,1)}%)")
    print(f"Sin traducir:          {tot_en - tot_es}  ({100*(tot_en-tot_es)//max(tot_en,1)}%)")
    print(f"QMs sin es_ES:         {no_es}")
    print()
    print(f"{'QM':45} {'total':>7} {'falta':>7}  estado")
    shown = rows if top is None else rows[:top]
    for name, total, missing, noes in shown:
        if missing == 0 and not noes:
            continue
        flag = "SIN es_ES" if noes else ""
        print(f"{name:45} {total:>7} {missing:>7}  {flag}")


def cef_scan():
    print("\n== Webviews CEF con literales chinos (CJK) ==")
    counts = {}
    for js in glob.glob(f"{WPS}/addons/**/*.js", recursive=True):
        if ".bak" in js:
            continue
        try:
            c = open(js, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        # quoted literals containing CJK, minus comments
        n = len(re.findall(r'"[^"\\\n]*[\u4e00-\u9fff][^"\\\n]*"', c))
        if n:
            addon = js.replace(WPS + "/addons/", "").split("/")[0]
            counts[addon] = counts.get(addon, 0) + n
    for addon, n in sorted(counts.items(), key=lambda x: -x[1])[:25]:
        print(f"  {addon:40} {n:>6} literales CJK")


def detail(qmname):
    pairs = find_qm_pairs()
    match = [k for k in pairs if qmname in k]
    for name in match:
        en, es = pairs[name]
        miss = qm_hashes(en) - (qm_hashes(es) if es else set())
        print(f"{name}: {len(miss)} hashes sin traducir")
        for h in sorted(miss)[:40]:
            print(f"  {h}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--cef" in args:
        cef_scan()
    elif "--qm" in args:
        detail(args[args.index("--qm") + 1])
    else:
        top = int(args[args.index("--top") + 1]) if "--top" in args else None
        coverage(top)
