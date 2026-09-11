"""Logika za preuzimanje i pretragu vijesti: Google News RSS pretraga po
ključnim riječima (glavni izvor) + dodatni klasični RSS feedovi portala."""
import html
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser

import db
from config import (
    EXTRA_FEEDS,
    GOOGLE_NEWS_CEID,
    GOOGLE_NEWS_GL,
    GOOGLE_NEWS_HL,
    KEYWORD_VARIATIONS,
    KEYWORDS,
)
from sentiment import analyze_sentiment

TAG_RE = re.compile(r"<[^>]+>")
GOOGLE_NEWS_SEARCH_URL = "https://news.google.com/rss/search"


def strip_html(text):
    if not text:
        return ""
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    return " ".join(text.split())


def build_google_news_url(keyword):
    """Generiše Google News RSS pretragu za ključnu riječ (kao tačnu frazu,
    radi preciznijih rezultata za višerječne ključne riječi).

    Format: https://news.google.com/rss/search?q=...&hl=sr&gl=BA&ceid=BA:sr
    """
    query = quote_plus(f'"{keyword}"')
    return (
        f"{GOOGLE_NEWS_SEARCH_URL}?q={query}"
        f"&hl={GOOGLE_NEWS_HL}&gl={GOOGLE_NEWS_GL}&ceid={GOOGLE_NEWS_CEID}"
    )


def get_google_news_feeds():
    """Za svaku ključnu riječ iz KEYWORDS generiše po jedan Google News RSS izvor."""
    return [
        {
            "name": f"Google News: {keyword}",
            "url": build_google_news_url(keyword),
            "channel": "google_news",
        }
        for keyword in KEYWORDS
    ]


def get_google_news_variation_feeds():
    """Za svaku varijaciju/sinonim iz KEYWORD_VARIATIONS generiše zaseban
    Google News RSS upit, da bi se proširila pokrivenost pretrage. Pronađeni
    članci se i dalje taguju prema tome koja riječ iz KEYWORDS liste je
    prisutna u naslovu/tekstu (ista logika kao za osnovnu pretragu)."""
    return [
        {
            "name": f"Google News (varijacija): {variation}",
            "url": build_google_news_url(variation),
            "channel": "google_news",
        }
        for variation in KEYWORD_VARIATIONS
    ]


def build_google_news_deep_url(keyword):
    """Ista Google News pretraga kao build_google_news_url, ali sa "when:30d"
    modifikatorom koji ograničava rezultate na posljednjih 30 dana - koristi
    se za dnevnu "duboku" provjeru koja hvata članke propuštene u redovnim
    (svaka 2h) provjerama."""
    query = quote_plus(f'"{keyword}" when:30d')
    return (
        f"{GOOGLE_NEWS_SEARCH_URL}?q={query}"
        f"&hl={GOOGLE_NEWS_HL}&gl={GOOGLE_NEWS_GL}&ceid={GOOGLE_NEWS_CEID}"
    )


def get_google_news_deep_feeds():
    """Dnevna 'duboka' pretraga (when:30d) za sve ključne riječi i njihove
    varijacije."""
    all_terms = KEYWORDS + KEYWORD_VARIATIONS
    return [
        {
            "name": f"Google News 30d: {term}",
            "url": build_google_news_deep_url(term),
            "channel": "google_news",
        }
        for term in all_terms
    ]


def get_extra_feeds():
    """Dodatni, ručno podešeni RSS feedovi portala iz config.py."""
    return [
        {"name": feed["name"], "url": feed["url"], "channel": "rss"}
        for feed in EXTRA_FEEDS
    ]


def parse_published_date(entry):
    """Pokušava da izvuče datum objave u obliku 'YYYY-MM-DD HH:MM:SS'."""
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value:
            try:
                return datetime(*value[:6]).isoformat(sep=" ")
            except Exception:
                pass

    raw = entry.get("published") or entry.get("updated") or ""
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            return dt.isoformat(sep=" ")
        except Exception:
            pass
    return raw


def extract_source_name(entry, fallback_name):
    """Google News stavke nose naziv originalnog portala u <source> elementu -
    koristimo ga umjesto generičkog naziva 'Google News' kad je dostupan."""
    source = entry.get("source")
    if source:
        title = source.get("title") if hasattr(source, "get") else None
        if title:
            return title
    return fallback_name


def process_feeds(feeds, found_at):
    """Obrađuje listu feedova (Google News pretrage i/ili klasični RSS),
    čuvajući članke koji sadrže bilo koju od ključnih riječi iz KEYWORDS u
    naslovu ili tekstu. Dedupliciranje se oslanja na postojeći UNIQUE(link,
    keyword) constraint u bazi (vidi db.insert_article) - isti članak se
    nikad ne upisuje dvaput bez obzira koja provjera (redovna ili duboka) ga
    je pronašla.

    Vraća broj novopronađenih (do sada nesačuvanih) članaka.
    """
    new_count = 0

    for feed in feeds:
        try:
            parsed = feedparser.parse(feed["url"])
        except Exception as exc:
            print(f"[press-clipping] Greška pri čitanju feeda '{feed['name']}': {exc}")
            continue

        for entry in parsed.entries:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            summary_raw = entry.get("summary") or entry.get("description") or ""
            summary = strip_html(summary_raw)
            haystack = f"{title} {summary}".lower()
            published_date = parse_published_date(entry)
            source_name = extract_source_name(entry, feed["name"])

            sentiment = analyze_sentiment(f"{title} {summary}")

            for keyword in KEYWORDS:
                if keyword.lower() in haystack:
                    added = db.insert_article(
                        title=title,
                        link=link,
                        source=source_name,
                        published_date=published_date,
                        snippet=summary[:200],
                        keyword=keyword,
                        found_at=found_at,
                        channel=feed["channel"],
                        sentiment=sentiment,
                    )
                    if added:
                        new_count += 1

    return new_count


def check_feeds():
    """Redovna provjera (pokreće se na svaka CHECK_INTERVAL_HOURS sata):
    Google News RSS pretraga za svaku ključnu riječ iz KEYWORDS i njenih
    varijacija (KEYWORD_VARIATIONS), plus dodatni RSS feedovi iz EXTRA_FEEDS.

    Vraća broj novopronađenih (do sada nesačuvanih) članaka.
    """
    found_at = datetime.now().isoformat(sep=" ", timespec="seconds")

    feeds = (
        get_google_news_feeds()
        + get_google_news_variation_feeds()
        + get_extra_feeds()
    )
    new_count = process_feeds(feeds, found_at)

    db.set_meta("last_check", found_at)
    db.set_meta("last_check_new_count", str(new_count))
    return new_count


def check_feeds_deep():
    """Dnevna 'duboka' provjera: Google News pretraga sa "when:30d"
    modifikatorom za sve ključne riječi i varijacije, da bi se uhvatili
    članci koje je redovna provjera (svaka 2h) možda propustila. Duplikati
    se prirodno preskaču zahvaljujući UNIQUE(link, keyword) constraint-u.

    Vraća broj novopronađenih (do sada nesačuvanih) članaka.
    """
    found_at = datetime.now().isoformat(sep=" ", timespec="seconds")

    feeds = get_google_news_deep_feeds()
    new_count = process_feeds(feeds, found_at)

    db.set_meta("last_check_deep", found_at)
    db.set_meta("last_check_deep_new_count", str(new_count))
    return new_count
