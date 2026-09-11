"""Pretraga YouTube videa (YouTube Data API v3, search endpoint) po ključnim
riječima iz config.py. Pronađeni videi se čuvaju u istu 'articles' tabelu
kao i RSS/Google News članci, sa channel='youtube'."""
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

import db
from config import KEYWORD_VARIATIONS, KEYWORDS
from sentiment import analyze_sentiment

load_dotenv()

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def parse_published_date(raw):
    """YouTube API vraća datum u ISO 8601 formatu (npr. 2024-05-01T12:34:56Z)."""
    if not raw:
        return ""
    try:
        dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
        return dt.isoformat(sep=" ")
    except ValueError:
        return raw


def search_youtube(keyword, max_results=10):
    """Poziva YouTube Data API v3 search endpoint za datu ključnu riječ.
    Vraća listu 'search result' stavki (raw JSON iz API-ja) ili praznu listu
    u slučaju greške."""
    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": max_results,
        "relevanceLanguage": "sr",
        "key": YOUTUBE_API_KEY,
    }
    try:
        response = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.RequestException as exc:
        print(f"[press-clipping] Greška pri pozivu YouTube API-ja za '{keyword}': {exc}")
        return []


def check_youtube():
    """Pretražuje YouTube za sve ključne riječi iz KEYWORDS i njihove
    varijacije iz KEYWORD_VARIATIONS, čuva pronađene video zapise u bazu
    (dedupliciranje preko postojećeg UNIQUE(link, keyword) constraint-a) i
    primjenjuje sentiment analizu na naslov+opis.

    Ako YOUTUBE_API_KEY nije podešen, samo loguje poruku i ne radi ništa
    (ne baca grešku).

    Vraća broj novopronađenih (do sada nesačuvanih) video zapisa.
    """
    if not YOUTUBE_API_KEY:
        print("YouTube API ključ nije podešen")
        return 0

    found_at = datetime.now().isoformat(sep=" ", timespec="seconds")
    all_terms = KEYWORDS + KEYWORD_VARIATIONS
    new_count = 0

    for term in all_terms:
        items = search_youtube(term)

        for item in items:
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            if not video_id or not snippet:
                continue

            title = (snippet.get("title") or "").strip()
            description = (snippet.get("description") or "").strip()
            channel_name = (snippet.get("channelTitle") or "YouTube").strip()
            published_date = parse_published_date(snippet.get("publishedAt"))
            link = f"https://www.youtube.com/watch?v={video_id}"

            haystack = f"{title} {description}".lower()
            sentiment = analyze_sentiment(f"{title} {description}")

            for keyword in KEYWORDS:
                if keyword.lower() in haystack:
                    added = db.insert_article(
                        title=title,
                        link=link,
                        source=channel_name,
                        published_date=published_date,
                        snippet=description[:200],
                        keyword=keyword,
                        found_at=found_at,
                        channel="youtube",
                        sentiment=sentiment,
                    )
                    if added:
                        new_count += 1

    db.set_meta("last_check_youtube", found_at)
    db.set_meta("last_check_youtube_new_count", str(new_count))
    return new_count
