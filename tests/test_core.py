"""
tests/test_core.py
Unit tests for sentiment analysis, keyword extraction, and the SQLite database layer.

Run with:
    python -m pytest tests/ -v
or without pytest:
    python tests/test_core.py
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.sentiment_analyzer import analyze_post, analyze_all, aggregate_sentiment, sentiment_by_subreddit
from utils.reddit_scraper import extract_keywords
from database import db as db_module

# ── Fixtures ─────────────────────────────────────────────────────────────────
POSTS_FIXTURE = [
    {"title": "AI startup raises $500M in record funding round", "text": "Investors are thrilled.", "subreddit": "technology", "score": 10000, "comments": 500, "url": ""},
    {"title": "Major data breach exposes millions of accounts", "text": "Users feel betrayed.", "subreddit": "technology", "score": 8000, "comments": 900, "url": ""},
    {"title": "Scientists discover new species of deep-sea fish", "text": "Findings published.", "subreddit": "science", "score": 5000, "comments": 200, "url": ""},
    {"title": "Stock markets crash amid global economic fears", "text": "Investors panic.", "subreddit": "business", "score": 12000, "comments": 1500, "url": ""},
    {"title": "New programming language promises 10x productivity", "text": "Community excited.", "subreddit": "programming", "score": 7000, "comments": 800, "url": ""},
]


# ── Sentiment analysis tests ─────────────────────────────────────────────────

def test_analyze_post_positive():
    post = {"title": "Wonderful news! Team celebrates fantastic victory with joy"}
    result = analyze_post(post)
    assert result["sentiment_label"] == "positive"
    assert result["sentiment_score"] > 0


def test_analyze_post_negative():
    post = {"title": "Terrible disaster kills hundreds, horrific scenes"}
    result = analyze_post(post)
    assert result["sentiment_label"] == "negative"
    assert result["sentiment_score"] < 0


def test_analyze_post_fields_present():
    post = {"title": "Test post", "text": ""}
    result = analyze_post(post)
    for field in ["sentiment_label", "sentiment_score", "sentiment_pos", "sentiment_neg", "sentiment_neu"]:
        assert field in result, f"Missing field: {field}"


def test_analyze_post_score_range():
    post = {"title": "Some neutral statement about things"}
    result = analyze_post(post)
    assert -1.0 <= result["sentiment_score"] <= 1.0


def test_aggregate_empty():
    result = aggregate_sentiment([])
    assert result["total"] == 0
    assert result["positive"] == 0


def test_aggregate_counts_match_total():
    analyzed = analyze_all(POSTS_FIXTURE)
    agg = aggregate_sentiment(analyzed)
    assert agg["positive"] + agg["negative"] + agg["neutral"] == agg["total"]
    assert agg["total"] == len(POSTS_FIXTURE)


def test_sentiment_by_subreddit_structure():
    analyzed = analyze_all(POSTS_FIXTURE)
    result = sentiment_by_subreddit(analyzed)
    assert isinstance(result, list)
    assert all("subreddit" in r and "avg_sentiment" in r for r in result)


# ── Keyword extraction tests ─────────────────────────────────────────────────

def test_extract_keywords_structure():
    result = extract_keywords(POSTS_FIXTURE, top_n=10)
    for item in result:
        assert "word" in item and "count" in item
        assert item["count"] >= 1


def test_extract_keywords_top_n():
    result = extract_keywords(POSTS_FIXTURE, top_n=5)
    assert len(result) <= 5


def test_extract_keywords_stopwords_removed():
    result = extract_keywords(POSTS_FIXTURE, top_n=20)
    stopwords = {"the", "and", "or", "of", "in", "a", "an"}
    for kw in result:
        assert kw["word"] not in stopwords


# ── Database tests ───────────────────────────────────────────────────────────
# Use a temporary, isolated database file so tests never touch trends.db

def _use_temp_db(tmp_path_str):
    db_module.DB_PATH = tmp_path_str


def test_database_init_and_save():
    test_db_path = os.path.join(tempfile.gettempdir(), "test_socialpulse.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    _use_temp_db(test_db_path)

    db_module.init_db()
    assert os.path.exists(test_db_path)

    sample = [{
        "title": "Test post", "subreddit": "technology", "score": 99,
        "comments": 3, "url": "https://reddit.com/x",
        "sentiment_label": "positive", "sentiment_score": 0.5,
    }]
    db_module.save_posts(sample)

    recent = db_module.get_recent_posts(limit=5)
    assert len(recent) == 1
    assert recent[0]["title"] == "Test post"
    assert recent[0]["sentiment_label"] == "positive"

    os.remove(test_db_path)


def test_database_sentiment_counts():
    test_db_path = os.path.join(tempfile.gettempdir(), "test_socialpulse2.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    _use_temp_db(test_db_path)

    db_module.init_db()
    sample = [
        {"title": "Pos", "subreddit": "technology", "score": 1, "comments": 0, "url": "", "sentiment_label": "positive", "sentiment_score": 0.5},
        {"title": "Neg", "subreddit": "technology", "score": 1, "comments": 0, "url": "", "sentiment_label": "negative", "sentiment_score": -0.5},
        {"title": "Neu", "subreddit": "technology", "score": 1, "comments": 0, "url": "", "sentiment_label": "neutral", "sentiment_score": 0.0},
    ]
    db_module.save_posts(sample)

    counts = db_module.get_sentiment_counts()
    assert counts["total"] == 3
    assert counts["positive"] == 1
    assert counts["negative"] == 1
    assert counts["neutral"] == 1

    os.remove(test_db_path)


def test_database_empty_counts():
    test_db_path = os.path.join(tempfile.gettempdir(), "test_socialpulse3.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    _use_temp_db(test_db_path)

    db_module.init_db()
    counts = db_module.get_sentiment_counts()
    assert counts["total"] == 0
    assert counts["positive"] == 0

    os.remove(test_db_path)


if __name__ == "__main__":
    import traceback
    tests = [fn for name, fn in list(globals().items()) if name.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗  {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
