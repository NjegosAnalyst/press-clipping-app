"""Jednostavna sentiment analiza bazirana na ključnim riječima (bez
eksternog API-ja). Prebrojava pogotke pozitivnih i negativnih riječi u
naslovu i isječku teksta članka i vraća "positive", "negative" ili
"neutral" na osnovu toga koja lista ima više pogodaka."""
import re

POSITIVE_WORDS = [
    # rekord
    "rekord", "rekordan", "rekordna", "rekordno", "rekordne", "rekordnih",
    # uspjeh/uspeh
    "uspjeh", "uspjesi", "uspjeha", "uspjehom", "uspeh", "uspesi", "uspeha",
    "uspješan", "uspješna", "uspješno", "uspješni", "uspješne",
    "uspešan", "uspešna", "uspešno", "uspešni", "uspešne",
    # nagrada
    "nagrada", "nagrade", "nagradu", "nagradom", "nagrada", "nagrađen",
    "nagrađena", "nagrađeno", "nagrađeni",
    # investicija
    "investicija", "investicije", "investiciju", "investicijom", "investicija",
    "investirati", "investirao", "investirala", "investitor", "investitori",
    # rast
    "rast", "rasta", "rastu", "rastom", "porast", "porasta", "porastao",
    "porasla", "poraslo", "raste",
    # otvaranje
    "otvaranje", "otvaranja", "otvaranju", "otvoren", "otvorena", "otvoreno",
    "otvoreni", "otvorenje",
    # proširenje
    "proširenje", "proširenja", "proširenju", "proširen", "proširena",
    "prošireno", "prošireni",
    # pohvala
    "pohvala", "pohvale", "pohvalu", "pohvalio", "pohvalila", "pohvaljen",
    "pohvaljena", "pohvaljeno",
    # najbolji
    "najbolji", "najbolja", "najbolje", "najboljih",
    # odličan
    "odličan", "odlična", "odlično", "odlični", "odlične",
    # zadovoljstvo
    "zadovoljstvo", "zadovoljstva", "zadovoljan", "zadovoljna", "zadovoljno",
    "zadovoljni",
    # priznanje
    "priznanje", "priznanja", "priznanju", "priznat", "priznata", "priznato",
    "priznati",
    # dobit
    "dobit", "dobiti", "dobit će", "dobitak", "dobitka",
    # unapređenje
    "unapređenje", "unapređenja", "unapređenju", "unaprijeđen", "unaprijeđena",
    "unaprijeđeno", "unapređen", "unapređena", "unapređeno",
]

NEGATIVE_WORDS = [
    # skandal
    "skandal", "skandala", "skandalu", "skandalom", "skandalozan",
    "skandalozna", "skandalozno",
    # afera
    "afera", "afere", "aferu", "aferom", "afera",
    # dug
    "dug", "duga", "dugu", "dugom", "dugovi", "dugova", "zadužen", "zadužena",
    "zaduženo", "zaduženi",
    # problem
    "problem", "problemi", "problema", "problemu", "problematičan",
    "problematična", "problematično",
    # žalba
    "žalba", "žalbe", "žalbu", "žalbom", "žalbi",
    # nesreća
    "nesreća", "nesreće", "nesreću", "nesrećom", "nesreći",
    # povreda
    "povreda", "povrede", "povredu", "povredom", "povrijeđen", "povrijeđena",
    "povrijeđeno", "povrijeđeni",
    # zatvaranje
    "zatvaranje", "zatvaranja", "zatvaranju", "zatvoren", "zatvorena",
    "zatvoreno", "zatvoreni",
    # kašnjenje
    "kašnjenje", "kašnjenja", "kašnjenju", "kasni", "kasnio", "kasnila",
    "kasnilo",
    # kvar
    "kvar", "kvara", "kvaru", "kvarom", "u kvaru", "pokvaren", "pokvarena",
    "pokvareno",
    # kritika
    "kritika", "kritike", "kritiku", "kritikom", "kritikovan", "kritikovana",
    "kritikovano", "kritikuje",
    # propust
    "propust", "propusta", "propustu", "propustom", "propušten", "propuštena",
    "propušteno",
    # istraga
    "istraga", "istrage", "istragu", "istragom", "istrazi",
    # tužba
    "tužba", "tužbe", "tužbu", "tužbom", "tuži", "tužen", "tužena", "tuženo",
    # gubitak
    "gubitak", "gubici", "gubitka", "gubitku", "gubitkom", "izgubljen",
    "izgubljena", "izgubljeno",
    # kolaps
    "kolaps", "kolapsa", "kolapsu", "kolapsom",
]

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text):
    return _WORD_RE.findall(text.lower())


def analyze_sentiment(text):
    """Prebrojava pogotke pozitivnih i negativnih riječi u datom tekstu
    (naslov + isječak) i vraća "positive", "negative" ili "neutral"."""
    if not text:
        return "neutral"

    words = _tokenize(text)
    positive_hits = sum(1 for w in words if w in POSITIVE_WORDS)
    negative_hits = sum(1 for w in words if w in NEGATIVE_WORDS)

    if positive_hits == 0 and negative_hits == 0:
        return "neutral"
    if positive_hits > negative_hits:
        return "positive"
    if negative_hits > positive_hits:
        return "negative"
    return "neutral"
