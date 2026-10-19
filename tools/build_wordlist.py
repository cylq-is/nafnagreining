"""Expand the hunspell-is dictionary (is.dic + is.aff) into a flat word list.

Source: https://github.com/nifgraup/hunspell-is (via LibreOffice/dictionaries),
licensed CC BY-SA 3.0.

Usage: python tools/build_wordlist.py [tools/hunspell-is] [src/nafnagreining/data/is_words.txt.gz]
"""

import gzip
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def parse_aff(path):
    """Return {flag: [(strip, add, cont_flags, cond_regex)]} for SFX rules."""
    rules = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts or parts[0] != "SFX":
            continue
        if len(parts) == 4 and parts[2] in ("Y", "N"):
            rules.setdefault(parts[1], [])  # header line
            continue
        flag, strip, add = parts[1], parts[2], parts[3]
        cond = parts[4] if len(parts) > 4 else "."  # condition may be omitted
        add, _, cont = add.partition("/")
        strip = "" if strip == "0" else strip
        add = "" if add == "0" else add
        cond_re = None if cond == "." else re.compile("(?:" + cond + ")$")
        rules[flag].append((strip, add, cont.split(",") if cont else [], cond_re))
    return rules


def apply_suffixes(word, flags, rules, depth):
    for flag in flags:
        for strip, add, cont, cond_re in rules.get(flag, ()):
            if strip and not word.endswith(strip):
                continue
            if cond_re and not cond_re.search(word):
                continue
            new = (word[: len(word) - len(strip)] if strip else word) + add
            if not new:
                continue
            yield new
            if cont and depth < 2:  # hunspell allows at most two suffixes
                yield from apply_suffixes(new, cont, rules, depth + 1)


def expand(dic_path, rules):
    words = set()
    lines = dic_path.read_text(encoding="utf-8").splitlines()[1:]  # first line is a count
    for line in lines:
        entry = line.split("\t", 1)[0].strip()
        if not entry:
            continue
        stem, _, flags = entry.partition("/")
        words.add(stem.lower())
        if flags:
            for form in apply_suffixes(stem, flags.split(","), rules, 1):
                words.add(form.lower())
    return words


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tools" / "hunspell-is"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "src" / "nafnagreining" / "data" / "is_words.txt.gz"
    rules = parse_aff(src / "is.aff")
    words = expand(src / "is.dic", rules)
    with gzip.open(out, "wt", encoding="utf-8") as f:
        f.write("\n".join(sorted(words)))
    print(f"{len(words)} word forms -> {out}")


if __name__ == "__main__":
    main()
