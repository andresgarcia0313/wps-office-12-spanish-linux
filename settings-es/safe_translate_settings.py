#!/usr/bin/env python3
"""Safely translate Chinese UI strings in WPS settings webview JS/HTML.

Strategy:
 - Only replace QUOTED string literals ("中文" or '中文'), so quotes act as
   boundaries and substrings of longer phrases are never corrupted.
 - Replace consistently everywhere (visible text AND logic comparisons stay
   in sync, since both sides use the same quoted literal).
 - Apply longest phrases first.
 - Validate each JS file with `node --check` before writing; revert on failure.
"""
import json, subprocess, sys, re, shutil, os

import os
_DICT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings_translations.json")
TRANSLATIONS = json.load(open(_DICT, encoding="utf-8")) if os.path.exists(_DICT) else {}


def translate_file(path):
    if not os.path.exists(path):
        return None
    orig = open(path, encoding='utf-8').read()
    text = orig
    # Longest first to avoid any phrase/substring ambiguity
    for zh in sorted(TRANSLATIONS, key=len, reverse=True):
        es = TRANSLATIONS[zh]
        # Only quoted literals: "..." and '...'
        text = text.replace(f'"{zh}"', f'"{es}"')
        text = text.replace(f"'{zh}'", f"'{es}'")
    if text == orig:
        return 0
    # Validate if JS
    if path.endswith('.js'):
        tmp = f"/tmp/wps_check_{os.getpid()}.js"
        open(tmp, 'w', encoding='utf-8').write(text)
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.remove(tmp)
        if r.returncode != 0:
            print(f"  VALIDATION FAILED for {path}: {r.stderr.strip()[:120]}")
            return -1
    open(path, 'w', encoding='utf-8').write(text)
    return text.count('  ') if False else 1


if __name__ == "__main__":
    for p in sys.argv[1:]:
        res = translate_file(p)
        print(f"{p}: {'OK' if res == 1 else ('no-change' if res == 0 else 'FAILED/skip')}")
