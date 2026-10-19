"""Icelandic language detection based on the hunspell-is word list."""

import gzip
import re
import unicodedata
from functools import lru_cache
from importlib.resources import files

WORDLIST = files(__package__) / "data" / "is_words.txt.gz"

TOKEN_RE = re.compile(r"[^\W\d_]+")
ICELANDIC_ONLY = set("þð")
ICELANDIC_ACCENTS = set("áéíóúýæö")
FOREIGN_LETTERS = set("øåäüßçñàèìòùâêîôûëïãõœšžčřłśźżőű")
RARE_LETTERS = set("cqwz")
# Common Faroese function words that are absent or archaic in modern Icelandic.
# Some are in the hunspell list anyway, and Faroese is the closest confusable language.
FAROESE_MARKERS = frozenset(
    "tað ið ella millum hetta hesin hesi hesar hesum eisini vóru tann teir tey sum at eg".split()
)


def _fold(word):
    """Strip diacritics so 'þetta' style text typed without accents can match."""
    word = word.replace("þ", "th").replace("ð", "d").replace("æ", "ae")
    return "".join(c for c in unicodedata.normalize("NFD", word) if not unicodedata.combining(c))


@lru_cache(maxsize=1)
def _words():
    with WORDLIST.open("rb") as raw, gzip.open(raw, "rt", encoding="utf-8") as f:
        words = frozenset(f.read().split("\n"))
    return words, frozenset(_fold(w) for w in words)


def score(s):
    """Return a score in roughly [-1, 1.5]; higher means more likely Icelandic."""
    tokens = TOKEN_RE.findall(s.lower())
    if not tokens:
        return float("-inf")
    words, folded = _words()
    letters = "".join(tokens)

    hits = sum(t in words for t in tokens)
    folded_hits = sum(t not in words and _fold(t) in folded for t in tokens)
    result = (hits + 0.5 * folded_hits) / len(tokens)

    if any(c in ICELANDIC_ONLY for c in letters):
        result += 0.3
    elif any(c in ICELANDIC_ACCENTS for c in letters):
        result += 0.1
    result -= 2.0 * sum(c in FOREIGN_LETTERS for c in letters) / len(tokens)
    result -= 0.5 * sum(c in RARE_LETTERS for c in letters) / len(tokens)
    result -= 1.0 * sum(t in FAROESE_MARKERS for t in tokens) / len(tokens)
    return result


THRESHOLD = 0.75


def isIcelandic(s):
    """Decide whether the text in s is Icelandic."""
    return score(s) >= THRESHOLD
