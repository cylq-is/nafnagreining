# nafnagreining

Icelandic language detection and extraction of person names, places and locations.

```python
>>> from nafnagreining import isIcelandic, extractEntities
>>> text = "Í dag fór ég í Hólavallakirkjugarð með Önnu móður minni. Hún kom frá Breiðholti."
>>> isIcelandic(text)
True
>>> extractEntities(text)
{'names': ['Anna'], 'places': ['Breiðholt'], 'locations': ['Hólavallakirkjugarður']}
```

- `isIcelandic(s) -> bool` decides whether a text is Icelandic. On random
  Wikipedia text in 13 languages it scores about 93% balanced accuracy. Faroese
  is the language it most often confuses with Icelandic.
- `extractEntities(s) -> Entities` returns a dict with the keys `names`,
  `places` and `locations`. Each key holds a list in the nominative
  ("Önnu" → "Anna", "Háskóla Íslands" → "Háskóli Íslands"), in order of first
  appearance and without duplicates. The input must be Icelandic, so check it
  with `isIcelandic` first.

## Install

From PyPI (once published):

```sh
pip install nafnagreining
uv add nafnagreining
```

Directly from git:

```sh
pip install "nafnagreining @ git+https://github.com/cylq-is/nafnagreining.git"
uv add "nafnagreining @ git+https://github.com/cylq-is/nafnagreining.git"
# a specific tag or commit:
uv add "nafnagreining @ git+https://github.com/cylq-is/nafnagreining.git@v0.1.0"
```

Requires Python 3.10+. The `islenska` dependency ships prebuilt wheels for
Linux (glibc, x86_64 and ARM64) and macOS. Other platforms have to compile it
from source, which needs a C++17 compiler.

## Development

```sh
uv sync                       # create .venv with the package and dev tools
uv run pytest -s              # run the tests and print accuracy reports
uv run python tests/test_icelandic.py --refresh   # re-download the Wikipedia test text
uv run python tools/build_wordlist.py             # rebuild the Icelandic word list
uv build                      # build sdist and wheel into dist/
uv publish                    # upload to PyPI (needs a PyPI token)
```

## Data and licences

The code is MIT licensed (see `LICENSE`).

- **Icelandic word list** (`src/nafnagreining/data/is_words.txt.gz`):
  generated from [hunspell-is](https://github.com/nifgraup/hunspell-is), which
  is based on Icelandic Wiktionary. Licensed CC BY-SA 3.0; see
  `src/nafnagreining/data/LICENSE-wordlist.txt`.
- **BÍN** (Beygingarlýsing íslensks nútímamáls), © Árni Magnússon Institute for
  Icelandic Studies, CC BY-SA 4.0. It is used through Miðeind's
  [islenska](https://pypi.org/project/islenska/) package and is not bundled here.
- **Test text** in `tests/data/wiki/` comes from Wikipedia (CC BY-SA 4.0) and
  is not included in the built package.
