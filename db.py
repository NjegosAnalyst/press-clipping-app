"""Sloj za rad sa bazom podataka.

Koristi PostgreSQL ako je postavljena DATABASE_URL environment varijabla
(produkcija, npr. Railway), inače pada nazad na lokalni SQLite fajl (lakše
lokalno testiranje bez dodatne infrastrukture).
"""
import os
import sqlite3
from datetime import date, timedelta

from config import DATABASE_PATH

DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL)

if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras


class _ConnWrapper:
    """Ujednačuje SQLite i psycopg2 konekcije iza istog execute/commit/close
    interfejsa i prevodi '?' placeholdere u '%s' kada se koristi Postgres,
    tako da ostatak modula ne mora da razlikuje bazu po upitu."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, query, params=()):
        cursor = self._conn.cursor()
        if IS_POSTGRES:
            query = query.replace("?", "%s")
        cursor.execute(query, params)
        return cursor

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_connection():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
    return _ConnWrapper(conn)


def init_db():
    conn = get_connection()
    if IS_POSTGRES:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                source TEXT NOT NULL,
                published_date TEXT,
                snippet TEXT,
                keyword TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT 'rss',
                found_at TEXT NOT NULL,
                sentiment TEXT,
                UNIQUE(link, keyword)
            )
            """
        )
    else:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                source TEXT NOT NULL,
                published_date TEXT,
                snippet TEXT,
                keyword TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT 'rss',
                found_at TEXT NOT NULL,
                UNIQUE(link, keyword)
            )
            """
        )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    if not IS_POSTGRES:
        # Migracije za SQLite baze kreirane prije uvođenja kolona "channel" i
        # "sentiment" (Postgres baze se uvijek kreiraju već sa ovim kolonama).
        try:
            conn.execute("ALTER TABLE articles ADD COLUMN channel TEXT NOT NULL DEFAULT 'rss'")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE articles ADD COLUMN sentiment TEXT")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def insert_article(title, link, source, published_date, snippet, keyword, found_at, channel="rss", sentiment=None):
    """Ubacuje članak ako već ne postoji (isti link + ključna riječ).
    Vraća True ako je novi red zaista dodan."""
    conn = get_connection()
    try:
        if IS_POSTGRES:
            cursor = conn.execute(
                """
                INSERT INTO articles
                    (title, link, source, published_date, snippet, keyword, channel, found_at, sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (link, keyword) DO NOTHING
                """,
                (title, link, source, published_date, snippet, keyword, channel, found_at, sentiment),
            )
        else:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO articles
                    (title, link, source, published_date, snippet, keyword, channel, found_at, sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, link, source, published_date, snippet, keyword, channel, found_at, sentiment),
            )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_sentiment(article_id, sentiment):
    conn = get_connection()
    conn.execute("UPDATE articles SET sentiment = ? WHERE id = ?", (sentiment, article_id))
    conn.commit()
    conn.close()


def query_articles(source=None, keyword=None, date_from=None, date_to=None, sentiment=None, channel=None, channel_in=None):
    conn = get_connection()
    query = "SELECT * FROM articles WHERE 1=1"
    params = []

    if source:
        query += " AND source = ?"
        params.append(source)
    if channel:
        query += " AND channel = ?"
        params.append(channel)
    if channel_in:
        placeholders = ",".join(["?"] * len(channel_in))
        query += f" AND channel IN ({placeholders})"
        params.extend(channel_in)
    if keyword:
        query += " AND keyword = ?"
        params.append(keyword)
    if date_from:
        query += " AND SUBSTR(published_date, 1, 10) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND SUBSTR(published_date, 1, 10) <= ?"
        params.append(date_to)
    if sentiment:
        query += " AND sentiment = ?"
        params.append(sentiment)

    query += " ORDER BY published_date DESC, id DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_distinct_sources():
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT source FROM articles ORDER BY source").fetchall()
    conn.close()
    return [row["source"] for row in rows]


def set_meta(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_meta(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def get_articles_by_day(days=30):
    """Broj članaka po danu za posljednjih `days` dana (uključujući dane bez
    ijednog članka, popunjene sa 0, radi neisprekidanog linijskog grafikona)."""
    conn = get_connection()
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """
        SELECT SUBSTR(published_date, 1, 10) AS day, COUNT(*) AS count
        FROM articles
        WHERE published_date IS NOT NULL AND published_date != ''
          AND SUBSTR(published_date, 1, 10) >= ?
        GROUP BY day
        """,
        (cutoff,),
    ).fetchall()
    conn.close()

    counts_by_day = {row["day"]: row["count"] for row in rows if row["day"]}

    today = date.today()
    result = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        day_str = day.isoformat()
        result.append({"day": day_str, "count": counts_by_day.get(day_str, 0)})
    return result


def get_top_sources(limit=10):
    """Top `limit` izvora po broju sačuvanih članaka."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT source, COUNT(*) AS count FROM articles GROUP BY source ORDER BY count DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [{"source": row["source"], "count": row["count"]} for row in rows]


def get_sentiment_distribution():
    """Broj članaka po sentimentu (pozitivno/neutralno/negativno)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT COALESCE(sentiment, 'neutral') AS sentiment, COUNT(*) AS count "
        "FROM articles GROUP BY COALESCE(sentiment, 'neutral')"
    ).fetchall()
    conn.close()

    distribution = {"positive": 0, "neutral": 0, "negative": 0}
    for row in rows:
        key = row["sentiment"] if row["sentiment"] in distribution else "neutral"
        distribution[key] += row["count"]
    return distribution


def get_channel_distribution():
    """Broj članaka po kanalu (google_news / rss / youtube)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT channel, COUNT(*) AS count FROM articles GROUP BY channel"
    ).fetchall()
    conn.close()
    return {row["channel"]: row["count"] for row in rows}
