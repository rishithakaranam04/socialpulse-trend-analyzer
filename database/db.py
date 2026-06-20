"""
db.py
SQLite database layer for SocialPulse.

SQLite stores the entire database in a single file (trends.db) that lives
in the project root. No separate database server is required.
"""

import sqlite3
import os
from datetime import datetime, timezone

# trends.db is created in the project root, one level above this file.
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "trends.db")


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the SQLite database.

    row_factory = sqlite3.Row lets us access columns by name
    (e.g. row['title']) instead of by index (e.g. row[0]).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create the posts table if it does not already exist.
    Safe to call every time the app starts — CREATE TABLE IF NOT EXISTS
    does nothing if the table is already there.
    """
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            subreddit       TEXT NOT NULL,
            score           INTEGER DEFAULT 0,
            num_comments    INTEGER DEFAULT 0,
            url             TEXT,
            sentiment_label TEXT,
            sentiment_score REAL,
            fetched_at      TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_posts(posts_list: list[dict]) -> None:
    """
    Insert a list of analyzed posts into the database.
    Called after every /api/analyze request so we build up history over time.
    """
    if not posts_list:
        return

    conn = get_connection()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    for post in posts_list:
        conn.execute(
            """
            INSERT INTO posts
                (title, subreddit, score, num_comments, url,
                 sentiment_label, sentiment_score, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post.get("title", ""),
                post.get("subreddit", ""),
                post.get("score", 0),
                post.get("comments", 0),
                post.get("url", ""),
                post.get("sentiment_label", "neutral"),
                post.get("sentiment_score", 0.0),
                timestamp,
            ),
        )

    conn.commit()
    conn.close()


def get_recent_posts(limit: int = 50) -> list[dict]:
    """Return the most recently saved posts, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM posts ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_sentiment_counts() -> dict:
    """
    Return all-time sentiment counts across every post ever saved.

    SUM(CASE WHEN ... THEN 1 ELSE 0 END) is SQL's way of writing
    conditional counting — for every row, add 1 if the condition is
    true, otherwise add 0.
    """
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive,
            SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative,
            SUM(CASE WHEN sentiment_label = 'neutral'  THEN 1 ELSE 0 END) AS neutral
        FROM posts
        """
    ).fetchone()
    conn.close()

    result = dict(row)
    # COUNT/SUM return None if the table is empty — normalize to 0
    return {k: (v if v is not None else 0) for k, v in result.items()}


def get_total_post_count() -> int:
    """Return the total number of posts ever saved (for a KPI card)."""
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS total FROM posts").fetchone()
    conn.close()
    return row["total"] or 0


def clear_all_posts() -> None:
    """
    Delete all rows from the posts table.
    Useful during development/testing to reset the database.
    """
    conn = get_connection()
    conn.execute("DELETE FROM posts")
    conn.commit()
    conn.close()


# ── Standalone test runner ──────────────────────────────────────────────────
# Run this file directly to verify the database layer works correctly:
#     python database/db.py
if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print(f"  Database file created at: {os.path.abspath(DB_PATH)}")

    print("\nSaving 3 sample posts...")
    sample_posts = [
        {"title": "Test post one", "subreddit": "technology", "score": 100,
         "comments": 10, "url": "https://reddit.com/1",
         "sentiment_label": "positive", "sentiment_score": 0.65},
        {"title": "Test post two", "subreddit": "science", "score": 200,
         "comments": 20, "url": "https://reddit.com/2",
         "sentiment_label": "negative", "sentiment_score": -0.42},
        {"title": "Test post three", "subreddit": "business", "score": 50,
         "comments": 5, "url": "https://reddit.com/3",
         "sentiment_label": "neutral", "sentiment_score": 0.0},
    ]
    save_posts(sample_posts)
    print("  Saved.")

    print("\nReading back recent posts:")
    for p in get_recent_posts(limit=5):
        print(f"  [{p['id']}] {p['title']} -> {p['sentiment_label']} ({p['sentiment_score']})")

    print("\nAll-time sentiment counts:")
    print(f"  {get_sentiment_counts()}")

    print("\n✅ Database module test PASSED")
