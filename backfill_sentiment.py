"""Jednokratni skript koji retroaktivno popunjava sentiment kolonu za sve
postojeće članke u bazi (koristi se jednom, nakon uvođenja sentiment analize)."""
from collections import Counter

import db
from sentiment import analyze_sentiment


def main():
    db.init_db()
    conn = db.get_connection()
    rows = conn.execute("SELECT id, title, snippet FROM articles").fetchall()

    counts = Counter()
    for row in rows:
        text = f"{row['title'] or ''} {row['snippet'] or ''}"
        sentiment = analyze_sentiment(text)
        conn.execute("UPDATE articles SET sentiment = ? WHERE id = ?", (sentiment, row["id"]))
        counts[sentiment] += 1

    conn.commit()
    conn.close()

    print(f"Ažurirano {len(rows)} članaka:")
    print(f"  Pozitivno: {counts.get('positive', 0)}")
    print(f"  Neutralno: {counts.get('neutral', 0)}")
    print(f"  Negativno: {counts.get('negative', 0)}")


if __name__ == "__main__":
    main()
