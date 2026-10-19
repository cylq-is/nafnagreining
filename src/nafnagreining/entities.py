"""Extract person names, places and locations from Icelandic text.

Uses BÍN (Beygingarlýsing íslensks nútímamáls, CC BY-SA 4.0) through Miðeind's
`islenska` package. BÍN tags proper nouns with a domain (hluti), e.g. `ism` for
Icelandic first names and `örn` for place names, and lists every inflected form,
so "Önnu" maps straight to the first name "Anna".

The input is assumed to be Icelandic (see icelandic.isIcelandic).
"""

import re
from functools import lru_cache
from typing import NamedTuple, TypedDict

from islenska import Bin

PERSON, PLACE, LOCATION = "person", "place", "location"

# BÍN domains (hluti) mapped to our three categories.
DOMAINS = {
    "ism": PERSON,  # Icelandic first names
    "föð": PERSON,  # patronymics (-son, -dóttir)
    "móð": PERSON,  # matronymics
    "gæl": PERSON,  # nicknames
    "ætt": PERSON,  # family names
    "örn": PLACE,  # place names
    "þor": PLACE,  # towns
    "bær": PLACE,  # farms
    "lönd": PLACE,  # countries and continents
    "erl": PLACE,  # foreign place names
    "svaedi": PLACE,  # regions and districts
    "heö": PLACE,  # neighbourhoods
    "göt": PLACE,  # streets and squares
    "fyr": LOCATION,  # institutions and companies
    "mvirk": LOCATION,  # buildings and structures
}

# Head words of compounds that BÍN only knows as common nouns, e.g. "Fjölskyldugarðurinn".
LOCATION_HEADS = (
    "safn", "kirkja", "höll", "skóli", "laug", "völlur", "spítali", "hús", "garður",
    "hótel", "stöð", "búð", "verslun", "torg", "bíó", "leikhús", "kaffihús", "bókasafn",
    "setur", "smiðja", "skáli", "stofa", "heimili",
)
PLACE_HEADS = (
    "vogur", "fjörður", "dalur", "nes", "vík", "fjall", "jökull", "foss", "eyri", "hverfi",
    "holt", "gata", "vegur", "braut", "hlíð", "heiði", "sveit", "eyja", "vatn", "fell",
    "strönd", "sýsla", "hreppur", "byggð", "staðir",
)

# Context words that point to a person or a place.
PLACE_PREPOSITIONS = {"í", "á", "úr", "frá", "til", "um", "við", "yfir", "undir", "að"}
STRONG_PLACE_PREPOSITIONS = {"í", "úr"}  # "í Hörpu" is a venue, never a person
PERSON_CONTEXT = {
    "með", "hjá", "herra", "frú", "séra",
    *"móðir móður föður faðir systir systur bróðir bróður sonur son syni sonar dóttir dóttur "
    "vinur vin vini vinar vinkona vinkonu vinkonur kona konu konan maður mann manni manns "
    "frændi frænda frænka frænku amma ömmu afi afa".split(),
}
# Nouns that refer to a man or a woman and agree with a name next to them in gender
# and case: "Helga bróður hennar" is "Helgi", "Helga systir hennar" is "Helga".
KIN_LEMMAS = frozenset(
    "móðir faðir systir bróðir sonur dóttir vinur vinkona frændi frænka amma afi "
    "mamma pabbi eiginmaður eiginkona kærasti kærasta kona maður".split()
)

# Function words: a capitalised sentence-initial word with one of these readings is
# just a normal word ("Hún", "Í", "Þegar"), not a name. Verbs, adjectives and numerals
# are left out on purpose, since "Helga", "Harpa" and "Einar" also have such readings.
CLOSED_CLASSES = {"pfn", "gr", "fs", "st", "nhm", "uh", "ao", "abfn"}
# Generic words that start a multi-word location name, e.g. "Hótel Sögu".
LOCATION_PREFIXES = {"hótel", "kaffi", "café", "gistiheimilið", "veitingastaðurinn"}

CASES = ("NF", "ÞGF", "ÞF", "EF")  # ÞGF before ÞF so prefix matching works
# Cases governed by common prepositions, used to pick the right reading of a name:
# "með Bjarna" is the dative of "Bjarni", not the nominative of the rare "Bjarna".
PREPOSITION_CASES = {
    "með": ("ÞGF", "ÞF"), "frá": ("ÞGF",), "hjá": ("ÞGF",), "af": ("ÞGF",), "úr": ("ÞGF",),
    "að": ("ÞGF",), "handa": ("ÞGF",), "gegn": ("ÞGF",), "um": ("ÞF",), "gegnum": ("ÞF",),
    "kringum": ("ÞF",), "til": ("EF",), "án": ("EF",), "meðal": ("EF",), "vegna": ("EF",),
    "milli": ("EF",), "við": ("ÞF", "ÞGF"), "eftir": ("ÞF", "ÞGF"), "fyrir": ("ÞF", "ÞGF"),
    "á": ("ÞF", "ÞGF"), "í": ("ÞF", "ÞGF"), "undir": ("ÞF", "ÞGF"), "yfir": ("ÞF", "ÞGF"),
}

TOKEN_RE = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*")
SENTENCE_END_RE = re.compile(r"[.!?:;„“\"«»\n]\s*$")


@lru_cache(maxsize=1)
def _bin():
    return Bin()


def _head_category(lemma):
    lemma = lemma.lower()
    if lemma.endswith(LOCATION_HEADS):
        return LOCATION
    if lemma.endswith(PLACE_HEADS):
        return PLACE
    return None


def _case(mark):
    """Grammatical case of a BÍN inflection tag, e.g. 'ÞGFET' -> 'ÞGF'."""
    return next((c for c in CASES if mark.startswith(c)), None)


class Reading(NamedTuple):
    """One BÍN interpretation of a word form, e.g. "Önnu" as the dative of "Anna"."""

    lemma: str
    gender: str
    case: str
    singular: bool
    core: bool  # BÍN core vocabulary ('K') rather than a rarer variant ('V')
    definite: bool  # has the suffixed article, e.g. "Húsdýragarðinn"
    category: str
    proper: bool  # a proper noun in BÍN, not a common noun classified by its head word


def _reading(m, category, proper=True):
    return Reading(
        m.ord, m.ofl, _case(m.mark), "FT" not in m.mark, m.birting == "K", "gr" in m.mark,
        category, proper,
    )


def _analyse(word, sentence_start):
    """Return (possible categories, is_genitive, readings) for a capitalised word."""
    _, meanings = _bin().lookup_ksnid(word, at_sentence_start=sentence_start)
    proper = [m for m in meanings if m.ord[:1].isupper()]
    if sentence_start and any(m.ofl in CLOSED_CLASSES for m in meanings if not m.ord[:1].isupper()):
        return set(), False, []

    readings = []
    for m in proper:
        for h in m.hluti.split(","):
            if h == "fyr" and _head_category(m.ord) == PLACE:
                readings.append(_reading(m, PLACE))  # BÍN files some streets as companies, e.g. "Hringbraut"
            elif h in DOMAINS:
                readings.append(_reading(m, DOMAINS[h]))
    categories = {r.category for r in readings}
    if sentence_start and categories == {LOCATION} and any(
        m.ofl in ("kk", "kvk", "hk") and not m.ord[:1].isupper() for m in meanings
    ):
        return set(), False, []  # "Fjölskyldan fór ..." is the family, not the company
    if not categories and not sentence_start:
        # Capitalised mid-sentence but only a common noun in BÍN: classify by head word.
        for m in meanings:
            category = _head_category(m.ord) if m.ofl in ("kk", "kvk", "hk") else None
            if category:
                readings.append(_reading(m, category, proper=False))
        categories = {r.category for r in readings}
    is_genitive = any("EF" in m.mark for m in meanings)
    return categories, is_genitive, readings


def _to_nominative(word, r):
    """Nominative of word under reading r, keeping number and article ("Elliðaánum" -> "Elliðaárnar")."""
    # Match BÍN's capitalisation: "Borgarspítali" is capitalised in BÍN, "fjölskyldugarður" isn't.
    source = word if r.lemma[:1].isupper() else word.lower()
    for v in _bin().lookup_variants(source, r.gender, "NF", lemma=r.lemma):
        if ("FT" not in v.mark) == r.singular and ("gr" in v.mark) == r.definite:
            form = v.bmynd
            break
    else:
        form = r.lemma
    return form[:1].upper() + form[1:]


@lru_cache(maxsize=1024)
def _kin_agreement(word):
    """(gender, case) pairs of a family noun such as "bróður", or an empty set."""
    if not word:
        return frozenset()
    _, meanings = _bin().lookup(word.lower())
    return frozenset((m.ofl, _case(m.mark)) for m in meanings if m.ord in KIN_LEMMAS)


POSSESSIVES = frozenset("minn þinn sinn vor".split())
GENITIVE_PRONOUNS = frozenset("hans hennar þess þeirra okkar ykkar".split())


@lru_cache(maxsize=1024)
def _is_possessive(word):
    """True for possessives such as "minn", "mína", "hennar"."""
    word = word.lower()
    if word in GENITIVE_PRONOUNS:
        return True
    return any(m.ord in POSSESSIVES for m in _bin().lookup(word)[1])


def _nominative(words, readings, previous, category, context=()):
    """Turn an inflected entity into the nominative: "Jóni Sigurðssyni" -> "Jón Sigurðsson".

    In a person name every part inflects; in a place or location only the head does
    ("Háskóla Íslands" -> "Háskóli Íslands"), or the name after a prefix ("Hótel Sögu"
    -> "Hótel Saga"). The inflecting parts share gender and case, so pick the
    (gender, case) that most of them agree on, then the case the preceding preposition
    governs, then BÍN's core vocabulary, then a form that already is nominative
    ("Helga" stays "Helga", not "Helgi"). Words BÍN doesn't know (e.g. "Laxness") are
    kept as written. `context` holds (gender, case) sets of neighbouring words that
    agree with the entity, such as "bróður" in "Helga bróður hennar"; each counts as
    one more part agreeing.
    """
    if category == PERSON:
        inflecting = range(len(words))
    elif words[0].lower() in LOCATION_PREFIXES:
        inflecting = range(1, len(words))
    else:
        inflecting = range(1)
    # Prefer readings in the entity's own category, e.g. "Esju" as the mountain, not the name.
    candidates = {
        i: [r for r in readings[i] if r.category == category] or readings[i] for i in inflecting
    }
    keys = {(r.gender, r.case) for rs in candidates.values() for r in rs}
    if not keys:
        return " ".join(words)
    governed = PREPOSITION_CASES.get((previous or "").lower(), ())

    def rank(key):
        matching = [r for rs in candidates.values() for r in rs if (r.gender, r.case) == key]
        support = sum(any((r.gender, r.case) == key for r in rs) for rs in candidates.values())
        support += sum(key in keys_of_neighbour for keys_of_neighbour in context)
        return (support, key[1] in governed, any(r.core for r in matching), key[1] == "NF")

    best = max(sorted(keys), key=rank)
    parts = list(words)
    for i, rs in candidates.items():
        options = [r for r in rs if (r.gender, r.case) == best]
        if options:
            # Prefer core vocabulary, then singular: "Katrínu" -> "Katrín", not "Katrína".
            parts[i] = _to_nominative(words[i], max(options, key=lambda r: (r.core, r.singular)))
    return " ".join(parts)


def _tokens(s):
    """Yield (word, sentence_start, previous_word) for every word in s."""
    previous, last_end = None, 0
    for match in TOKEN_RE.finditer(s):
        gap = s[last_end:match.start()]
        sentence_start = previous is None or bool(SENTENCE_END_RE.search(gap))
        yield match.group(), sentence_start, previous
        previous, last_end = match.group(), match.end()


def _resolve(categories, previous, following, neighbour_is_person):
    """Pick one category for a word that BÍN lists under several domains."""
    prev = (previous or "").lower()
    nxt = (following or "").lower()
    if PERSON in categories and len(categories) == 1:
        # "tónleikar í Hörpu": a name after í/úr is a venue that BÍN only knows as a name.
        return LOCATION if prev in STRONG_PLACE_PREPOSITIONS else PERSON
    if len(categories) == 1:
        return next(iter(categories))
    if PERSON in categories and (prev in PERSON_CONTEXT or nxt in PERSON_CONTEXT or neighbour_is_person):
        return PERSON
    if prev in PLACE_PREPOSITIONS:
        return PLACE if PLACE in categories else LOCATION
    for category in (PERSON, PLACE, LOCATION):
        if category in categories:
            return category


class Entities(TypedDict):
    names: list[str]
    places: list[str]
    locations: list[str]


def extractEntities(s) -> Entities:
    """Return the names, places and locations found in the Icelandic text s.

    For example {"names": ["Anna"], "places": ["Breiðholt"], "locations": ["Harpa"]}.
    Everything is given in the nominative ("Önnu" -> "Anna", "Breiðholti" ->
    "Breiðholt", "Háskóla Íslands" -> "Háskóli Íslands"). Each list is in order
    of first appearance, without duplicates. Multi-word names such as
    "Jón Sigurðsson" and "Háskóli Íslands" are kept together.
    """
    tokens = list(_tokens(s))
    analysed = []  # (word, categories, is_genitive, sentence_start, previous, readings)
    for word, sentence_start, previous in tokens:
        if word[0].isupper():
            analysis = _analyse(word, sentence_start)
        else:
            analysis = set(), False, []
        analysed.append((word, analysis[0], analysis[1], sentence_start, previous, analysis[2]))

    spans = []  # [category, [words], index of last word, index of first word]
    for i, (word, categories, genitive, sentence_start, previous, _) in enumerate(analysed):
        last = spans[-1] if spans else None
        joins = last is not None and last[2] == i - 1 and not sentence_start and word[0].isupper()
        if not categories and not (joins and last[0] == PERSON):
            if word.lower() in LOCATION_PREFIXES and word[0].isupper():
                spans.append([LOCATION, [word], i, i])
            continue
        following = analysed[i + 1][0] if i + 1 < len(analysed) else None
        adjacent = [analysed[j][1] for j in (i - 1, i + 1) if 0 <= j < len(analysed)]
        neighbour_is_person = any(c == {PERSON} for c in adjacent)
        category = _resolve(categories, previous, following, neighbour_is_person) if categories else None

        if joins and last[0] == PERSON:
            last[1].append(word)  # "Jóni" + "Sigurðssyni", "Halldór" + "Laxness"
        elif joins and last[0] == LOCATION and last[1][-1].lower() in LOCATION_PREFIXES:
            last[1].append(word)  # "Hótel" + "Sögu"
        elif joins and last[0] == LOCATION and genitive and category == PLACE:
            last[1].append(word)  # "Háskóla" + "Íslands"
        else:
            spans.append([category, [word], i, i])
            continue
        last[2] = i

    result = {PERSON: [], PLACE: [], LOCATION: []}
    for category, words, end, start in spans:
        readings = [a[5] for a in analysed[start:end + 1]]
        context = ()
        if category == PERSON:
            # "Helga bróður hennar", "systur minni Önnu"
            before = [start - 1]
            if start >= 2 and _is_possessive(analysed[start - 1][0]):
                before.append(start - 2)  # "bróður minn Helga"
            neighbours = [analysed[j][0] for j in (*before, end + 1) if 0 <= j < len(analysed)]
            context = [k for k in map(_kin_agreement, neighbours) if k]
        text = _nominative(words, readings, analysed[start][4], category, context)
        if text not in result[category]:
            result[category].append(text)
    return {"names": result[PERSON], "places": result[PLACE], "locations": result[LOCATION]}
