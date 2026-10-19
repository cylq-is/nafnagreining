"""Accuracy test for isIcelandic() against random Wikipedia text.

Run: uv run pytest tests/test_icelandic.py -s          (uses cached text in tests/data/wiki/)
     uv run python tests/test_icelandic.py --refresh   (downloads new random articles)
"""

import json
import random
import re
import sys
import time
import unittest
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

from nafnagreining import isIcelandic

CACHE = Path(__file__).parent / "data" / "wiki"
OTHER_LANGS = ["fo", "da", "nb", "nn", "sv", "de", "nl", "en", "fi", "fr", "es", "pl"]
ARTICLES_PER_LANG = 60
TARGET_ACCURACY = 0.85
USER_AGENT = "isIcelandic-eval/0.1 (language detection test script)"


def fetch_extracts(lang, count):
    """Fetch plain-text intro extracts of random articles from one Wikipedia."""
    host = "no" if lang == "nb" else lang
    extracts = []
    while len(extracts) < count:
        params = {
            "action": "query", "format": "json", "generator": "random",
            "grnnamespace": 0, "grnlimit": 20, "prop": "extracts",
            "exintro": 1, "explaintext": 1, "exlimit": 20,
        }
        url = f"https://{host}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    pages = json.load(resp)["query"]["pages"].values()
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 5:
                    raise
                time.sleep(int(e.headers.get("Retry-After") or 0) or 5 * 2 ** attempt)
        time.sleep(1)  # be polite to the API
        extracts += [p["extract"] for p in pages if len(p.get("extract", "").split()) >= 8]
    return extracts[:count]


def load_corpus(refresh=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    corpus = {}
    for lang in ["is"] + OTHER_LANGS:
        path = CACHE / f"{lang}.json"
        if refresh or not path.exists():
            print(f"fetching {lang}.wikipedia.org ...", file=sys.stderr)
            path.write_text(json.dumps(fetch_extracts(lang, ARTICLES_PER_LANG), ensure_ascii=False))
        corpus[lang] = json.loads(path.read_text())
    return corpus


def make_samples(text, rng):
    """Cut one article intro into a short snippet, a sentence and a paragraph."""
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if len(s.split()) >= 4]
    start = rng.randrange(max(1, len(words) - 4))
    samples = {"short (3-5 words)": " ".join(words[start:start + rng.randint(3, 5)])}
    if sentences:
        samples["sentence"] = rng.choice(sentences)
    samples["paragraph"] = text[:600]
    return samples


def evaluate(corpus):
    rng = random.Random(1)
    cases = []  # (lang, length, text)
    for lang, texts in corpus.items():
        for text in texts:
            cases += [(lang, length, s) for length, s in make_samples(text, rng).items()]

    by_lang, by_length = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    errors = []
    for lang, length, text in cases:
        ok = isIcelandic(text) == (lang == "is")
        for bucket in (by_lang[lang], by_length[length]):
            bucket[0] += ok
            bucket[1] += 1
        if not ok:
            errors.append((lang, text))

    # Weight Icelandic and non-Icelandic equally so the many foreign samples don't dominate.
    is_acc = by_lang["is"][0] / by_lang["is"][1]
    other = [sum(by_lang[l][i] for l in OTHER_LANGS) for i in (0, 1)]
    other_acc = other[0] / other[1]
    balanced = (is_acc + other_acc) / 2

    print("\nAccuracy per language (is = correctly accepted, others = correctly rejected)")
    for lang in ["is"] + OTHER_LANGS:
        ok, n = by_lang[lang]
        print(f"  {lang:4} {ok / n:7.1%}  ({ok}/{n})")
    print("Accuracy per text length")
    for length, (ok, n) in by_length.items():
        print(f"  {length:18} {ok / n:7.1%}  ({ok}/{n})")
    print(f"\nIcelandic recall:       {is_acc:.1%}")
    print(f"Non-Icelandic rejected: {other_acc:.1%}")
    print(f"Balanced accuracy:      {balanced:.1%}  (target {TARGET_ACCURACY:.0%})")
    print("\nSample errors:")
    for lang, text in random.Random(2).sample(errors, min(10, len(errors))):
        print(f"  [{lang}] {text[:90]!r}")
    return balanced


class TestIsIcelandic(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(isIcelandic("Ég fór út í búð að kaupa mjólk og brauð."))
        self.assertFalse(isIcelandic("I went to the shop to buy milk and bread."))
        self.assertFalse(isIcelandic("Jeg gik ned i butikken for at købe mælk."))
        self.assertFalse(isIcelandic(""))
        self.assertFalse(isIcelandic("12345 !!!"))

    def test_wikipedia_accuracy(self):
        accuracy = evaluate(load_corpus(refresh="--refresh" in sys.argv))
        self.assertGreaterEqual(accuracy, TARGET_ACCURACY)


if __name__ == "__main__":
    unittest.main(argv=[a for a in sys.argv if a != "--refresh"], verbosity=2)
