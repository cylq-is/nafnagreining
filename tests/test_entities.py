"""Accuracy test for extractEntities() on hand-annotated Icelandic sentences.

Expected names, places and locations are all in the nominative.

Run: uv run pytest tests/test_entities.py -s
"""

import unittest

from nafnagreining import extractEntities

# (sentence, names, places, locations)
CASES = [
    ("Í dag fór ég í Hólavallakirkjugarð með Önnu móður minni til þess að skoða leiðin. "
     "Hún kom frá Breiðholti til þess að vera með mér",
     ["Anna"], ["Breiðholt"], ["Hólavallakirkjugarður"]),
    ("Jón Sigurðsson fæddist á Hrafnseyri við Arnarfjörð.",
     ["Jón Sigurðsson"], ["Hrafnseyri", "Arnarfjörður"], []),
    ("Við fórum á tónleika í Hörpu og svo á kaffihús á Laugavegi.",
     [], ["Laugavegur"], ["Harpa"]),
    ("Björk Guðmundsdóttir býr í Reykjavík en Sigga frænka hennar á Akureyri.",
     ["Björk Guðmundsdóttir", "Sigga"], ["Reykjavík", "Akureyri"], []),
    ("Hann stundar nám við Háskóla Íslands og vinnur á Landspítalanum.",
     [], [], ["Háskóli Íslands", "Landspítalinn"]),
    ("Við gengum á Esju og keyrðum svo til Hafnarfjarðar.",
     [], ["Esja", "Hafnarfjörður"], []),
    ("Guðrún og Pétur giftu sig í Hallgrímskirkju í fyrra.",
     ["Guðrún", "Pétur"], [], ["Hallgrímskirkja"]),
    ("Amma mín, Sigríður Jónsdóttir, ólst upp á Ísafirði.",
     ["Sigríður Jónsdóttir"], ["Ísafjörður"], []),
    ("Krakkarnir fóru í sund í Laugardalslaug eftir skóla.",
     [], [], ["Laugardalslaug"]),
    ("Ólafur keyrði frá Selfossi til Víkur í gær.",
     ["Ólafur"], ["Selfoss", "Vík"], []),
    ("Þegar ég var lítill bjó ég í Breiðholti hjá ömmu minni.",
     [], ["Breiðholt"], []),
    ("Sumarið 2019 ferðuðumst við um Vestfirði og gistum á Patreksfirði.",
     [], ["Vestfirðir", "Patreksfjörður"], []),
    ("Helga hitti Kristján bróður sinn í Kringlunni.",
     ["Helga", "Kristján"], ["Kringlan"], []),
    ("Hekla gaus árið 2000 og askan barst alla leið til Noregs.",
     [], ["Hekla", "Noregur"], []),
    ("Dagur fór með Önnu í Þjóðleikhúsið á laugardaginn.",
     ["Dagur", "Anna"], [], ["Þjóðleikhúsið"]),
    ("Ég keypti mjólk í Bónus á Hringbraut.",
     [], ["Hringbraut"], ["Bónus"]),
    ("Einar Benediktsson orti mörg ljóð um Ísland.",
     ["Einar Benediktsson"], ["Ísland"], []),
    ("Ferðamennirnir skoðuðu Gullfoss og Geysi og enduðu daginn á Þingvöllum.",
     [], ["Gullfoss", "Geysir", "Þingvellir"], []),
    ("Vigdís Finnbogadóttir var forseti Íslands frá 1980 til 1996.",
     ["Vigdís Finnbogadóttir"], ["Ísland"], []),
    ("Systir mín flutti til Kaupmannahafnar í Danmörku í fyrra.",
     [], ["Kaupmannahöfn", "Danmörk"], []),
    ("Siggi og Nonni léku sér á Klambratúni allan daginn.",
     ["Siggi", "Nonni"], ["Klambratún"], []),
    ("Hún fór í Smáralind með Katrínu vinkonu sinni.",
     ["Katrín"], [], ["Smáralind"]),
    ("Á morgun fljúgum við frá Keflavík til London.",
     [], ["Keflavík", "London"], []),
    ("Halldór Laxness bjó á Gljúfrasteini í Mosfellsdal.",
     ["Halldór Laxness"], ["Mosfellsdalur"], ["Gljúfrasteinn"]),
    ("Kennarinn í Hlíðaskóla heitir Arnar.",
     ["Arnar"], [], ["Hlíðaskóli"]),
    ("Við borðuðum hádegismat á Hótel Sögu og fórum svo á Þjóðminjasafnið.",
     [], [], ["Hótel Saga", "Þjóðminjasafnið"]),
    ("Fjölskyldan fór í Húsdýragarðinn og svo í heimsókn til Jóhönnu frænku.",
     ["Jóhanna"], [], ["Húsdýragarðurinn"]),
    ("Snorri Sturluson bjó í Reykholti í Borgarfirði.",
     ["Snorri Sturluson"], ["Reykholt", "Borgarfjörður"], []),
    ("Bíllinn bilaði á Holtavörðuheiði á leiðinni norður.",
     [], ["Holtavörðuheiði"], []),
    ("Harpa og Hrafn eiga heima í Kópavogi.",
     ["Harpa", "Hrafn"], ["Kópavogur"], []),
    ("Leikurinn fer fram á Laugardalsvelli á sunnudaginn.",
     [], [], ["Laugardalsvöllur"]),
    ("Það rigndi mikið í Vestmannaeyjum um helgina.",
     [], ["Vestmannaeyjar"], []),
    ("Margrét vinnur í Landsbankanum í Austurstræti.",
     ["Margrét"], ["Austurstræti"], ["Landsbankinn"]),
    ("Ég las bók eftir Arnald Indriðason á Akranesi.",
     ["Arnaldur Indriðason"], ["Akranes"], []),
    ("Vatnajökull er stærsti jökull Evrópu.",
     [], ["Vatnajökull", "Evrópa"], []),
    ("Strákarnir æfa fótbolta með Val á Hlíðarenda.",
     [], ["Hlíðarendi"], []),
    ("Þórunn og Gunnar heimsóttu Bessastaði í vor.",
     ["Þórunn", "Gunnar"], ["Bessastaðir"], []),
    ("Pabbi fór á sjóinn frá Grindavík en mamma var heima.",
     [], ["Grindavík"], []),
    ("Tónleikarnir verða í Hofi á Akureyri.",
     [], ["Akureyri"], ["Hof"]),
    ("Ég og Elín sáum norðurljósin við Jökulsárlón.",
     ["Elín"], ["Jökulsárlón"], []),
]

# Inflected names that must come back in the nominative.
NOMINATIVE = [
    ("Ég fór með Önnu í veiðiferð", ["Anna"]),
    ("Ég talaði við Jóni Sigurðssyni.", ["Jón Sigurðsson"]),
    ("Bréfið var frá Helga Jónssyni.", ["Helgi Jónsson"]),
    ("Helga fór heim.", ["Helga"]),
    ("Ég hitti Helgu og Bjarna.", ["Helga", "Bjarni"]),
    ("Hann gaf Ragnheiði Jónsdóttur blóm.", ["Ragnheiður Jónsdóttir"]),
    ("Við fórum til Siggu frænku og Önnu.", ["Sigga", "Anna"]),
    ("Anna hitti Önnu.", ["Anna"]),
    # A family noun next to the name settles its gender: Helgi (m.) or Helga (f.).
    ("Ég fór með Önnu Jónsdóttur og Helga bróður hennar til Akureyrar.", ["Anna Jónsdóttir", "Helgi"]),
    ("Helga systir hennar kom líka.", ["Helga"]),
    ("Ég hitti Helga bróður minn.", ["Helgi"]),
    ("Ég talaði við bróður minn Helga.", ["Helgi"]),
    ("Ég fór til vinkonu minnar Helgu.", ["Helga"]),
    ("Ég sá Bjarna frænda minn.", ["Bjarni"]),
]

# Places and locations in the nominative, keeping number and the suffixed article.
NOMINATIVE_PLACES = [
    ("Hún kom frá Breiðholti.", ["Breiðholt"], []),
    ("Við gistum í Vestmannaeyjum.", ["Vestmannaeyjar"], []),
    ("Afi veiddi í Elliðaánum.", ["Elliðaárnar"], []),
    ("Hann vinnur við Háskóla Íslands.", [], ["Háskóli Íslands"]),
    ("Við fórum í Húsdýragarðinn.", [], ["Húsdýragarðurinn"]),
    ("Við borðuðum á Hótel Sögu.", [], ["Hótel Saga"]),
    ("Tónleikarnir voru í Hörpu.", [], ["Harpa"]),
    ("Við gengum á Esju.", ["Esja"], []),
]

# Written after the rules were tuned on CASES, and never tuned on: an honest estimate.
HELD_OUT = [
    ("Ragnheiður og Ásgeir fluttu frá Egilsstöðum til Reykjanesbæjar.",
     ["Ragnheiður", "Ásgeir"], ["Egilsstaðir", "Reykjanesbær"], []),
    ("Við heimsóttum Listasafn Reykjavíkur með Steinunni frænku.",
     ["Steinunn"], [], ["Listasafn Reykjavíkur"]),
    ("Bróðir minn, Hallgrímur Pétursson, býr á Siglufirði.",
     ["Hallgrímur Pétursson"], ["Siglufjörður"], []),
    ("Hópurinn gekk upp á Snæfellsjökul í gær.",
     [], ["Snæfellsjökull"], []),
    ("Fundurinn verður haldinn í Ráðhúsi Reykjavíkur á mánudaginn.",
     [], [], ["Ráðhús Reykjavíkur"]),
    ("Kristín hringdi í Bjarna frá Húsavík.",
     ["Kristín", "Bjarni"], ["Húsavík"], []),
    ("Ég ólst upp í Hafnarfirði en bý núna í Garðabæ.",
     [], ["Hafnarfjörður", "Garðabær"], []),
    ("Unnur fór með dóttur sína í Fjölskyldugarðinn.",
     ["Unnur"], [], ["Fjölskyldugarðurinn"]),
    ("Á leiðinni til Akureyrar stoppuðum við í Borgarnesi.",
     [], ["Akureyri", "Borgarnes"], []),
    ("Sveinn Björnsson var fyrsti forseti lýðveldisins.",
     ["Sveinn Björnsson"], [], []),
    ("Tónlistarskólinn í Kópavogi heldur tónleika í Salnum.",
     [], ["Kópavogur"], ["Tónlistarskólinn", "Salurinn"]),
    ("Þau gengu meðfram Tjörninni og settust á bekk á Austurvelli.",
     [], ["Tjörnin", "Austurvöllur"], []),
    ("Lára keypti nýja skó í Kringlunni.",
     ["Lára"], ["Kringlan"], []),
    ("Afi minn veiddi lax í Elliðaánum.",
     [], ["Elliðaárnar"], []),
    ("Bergþóra vinnur á Borgarspítalanum en Guðni kennir í Menntaskólanum í Reykjavík.",
     ["Bergþóra", "Guðni"], ["Reykjavík"], ["Borgarspítalinn", "Menntaskólinn"]),
    ("Stelpurnar syntu í Sundhöll Reykjavíkur.",
     [], [], ["Sundhöll Reykjavíkur"]),
    ("Eyjafjallajökull gaus árið 2010.",
     [], ["Eyjafjallajökull"], []),
    ("Ég hitti Jónas og Sólveigu á Ingólfstorgi.",
     ["Jónas", "Sólveig"], ["Ingólfstorg"], []),
    ("Mamma fæddist í Stykkishólmi en pabbi í Noregi.",
     [], ["Stykkishólmur", "Noregur"], []),
    ("Hjálmar fór í Bláa lónið með Þóru.",
     ["Hjálmar", "Þóra"], ["Bláa lónið"], []),
]

LABELS = ("names", "places", "locations")


def evaluate(cases=CASES, title="Tuning set"):
    """Print per-category precision/recall and the share of fully correct sentences."""
    counts = {label: [0, 0, 0] for label in LABELS}  # true positives, predicted, expected
    exact = 0
    print(f"\n=== {title} ({len(cases)} sentences) ===")
    for sentence, *expected in cases:
        got = [extractEntities(sentence)[label] for label in LABELS]
        if [sorted(g) for g in got] == [sorted(e) for e in expected]:
            exact += 1
        else:
            print(f"\n  {sentence}")
        for label, g, e in zip(LABELS, got, expected):
            counts[label][0] += len(set(g) & set(e))
            counts[label][1] += len(g)
            counts[label][2] += len(e)
            if set(g) != set(e):
                print(f"    {label:9} expected {e}  got {g}")

    print("\nPer category            precision  recall     F1")
    tp_all = pred_all = exp_all = 0
    for label, (tp, pred, exp) in counts.items():
        p, r = tp / max(pred, 1), tp / max(exp, 1)
        print(f"  {label:20} {p:9.1%} {r:8.1%} {2 * p * r / max(p + r, 1e-9):7.1%}")
        tp_all, pred_all, exp_all = tp_all + tp, pred_all + pred, exp_all + exp
    p, r = tp_all / pred_all, tp_all / exp_all
    f1 = 2 * p * r / (p + r)
    print(f"  {'all entities':20} {p:9.1%} {r:8.1%} {f1:7.1%}")
    print(f"\nSentences fully correct: {exact}/{len(cases)} ({exact / len(cases):.1%})")
    return f1


class TestExtractEntities(unittest.TestCase):
    def test_example(self):
        self.assertEqual(
            extractEntities(CASES[0][0]),
            {"names": ["Anna"], "places": ["Breiðholt"], "locations": ["Hólavallakirkjugarður"]},
        )

    def test_nominative(self):
        for sentence, names in NOMINATIVE:
            with self.subTest(sentence=sentence):
                self.assertEqual(extractEntities(sentence)["names"], names)

    def test_nominative_places(self):
        for sentence, places, locations in NOMINATIVE_PLACES:
            with self.subTest(sentence=sentence):
                got = extractEntities(sentence)
                self.assertEqual((got["places"], got["locations"]), (places, locations))

    def test_empty(self):
        self.assertEqual(extractEntities(""), {"names": [], "places": [], "locations": []})

    def test_accuracy(self):
        self.assertGreaterEqual(evaluate(), 0.85)

    def test_held_out_accuracy(self):
        self.assertGreaterEqual(evaluate(HELD_OUT, "Held-out set"), 0.85)


if __name__ == "__main__":
    unittest.main(verbosity=2)
