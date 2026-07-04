"""
app.py — SocialPulse: Reddit Trend & Sentiment Analyzer
Flask backend. Routes:
  GET /              -> dashboard page
  GET /api/analyze   -> fetch + analyze + save + return JSON
  GET /api/history   -> recent posts from the database
  GET /api/health    -> health check
"""

import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from utils.news_scraper import fetch_trending_posts, extract_keywords
from utils.sentiment_analyzer import analyze_all, aggregate_sentiment, sentiment_by_subreddit
from utils.wordcloud_gen import generate_wordcloud_base64
from database.db import init_db, save_posts, get_recent_posts, get_sentiment_counts, get_total_post_count

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-prod")
CORS(app)

# Create the posts table on startup if it doesn't already exist.
init_db()

DEFAULT_SUBREDDITS = os.getenv(
    "DEFAULT_CATEGORIES",
    "technology,worldnews,business,science,programming"
).split(",")

DEFAULT_LIMIT = int(os.getenv("DEFAULT_POST_LIMIT", "50"))


def _serialize_post(p: dict) -> dict:
    """Make sure every value in a post dict is JSON-safe."""
    out = dict(p)
    if not isinstance(out.get("created_utc"), str):
        out["created_utc"] = str(out.get("created_utc", ""))
    return out


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze")
def analyze():
    """
    Main pipeline: fetch Reddit posts -> run VADER sentiment ->
    save to SQLite -> return aggregated JSON for the dashboard.
    """
    raw_subs = request.args.get("subreddits", ",".join(DEFAULT_SUBREDDITS))
    subreddits = [s.strip() for s in raw_subs.split(",") if s.strip()]
    limit = min(int(request.args.get("limit", DEFAULT_LIMIT)), 100)

    # 1. Fetch posts from Reddit (or mock data if no credentials configured)
    posts = fetch_trending_posts(subreddits, limit)

    # 2. Run VADER sentiment analysis on each post
    analyzed = analyze_all(posts)

    # 3. Persist to SQLite so we build up history over time
    save_posts(analyzed)

    # 4. Build response payload
    sentiment_summary = aggregate_sentiment(analyzed)
    sub_sentiment = sentiment_by_subreddit(analyzed)
    keywords = extract_keywords(posts, top_n=20)
    wordcloud_b64 = generate_wordcloud_base64(posts)
    all_time_counts = get_sentiment_counts()
    all_time_total = get_total_post_count()

    sub_dist: dict[str, int] = {}
    for p in analyzed:
        sub_dist[p["subreddit"]] = sub_dist.get(p["subreddit"], 0) + 1

    def _interleave_by_category(posts, total=10):
        buckets = {}
        for p in posts:
            buckets.setdefault(p["subreddit"], []).append(p)
        result = []
        while len(result) < total and any(buckets.values()):
            for key in list(buckets.keys()):
                if buckets[key]:
                    result.append(buckets[key].pop(0))
                if len(result) >= total:
                    break
        return result

    top_posts = _interleave_by_category(analyzed, total=10)

    return jsonify({
        "status": "ok",
        "meta": {
            "subreddits": subreddits,
            "total_posts": len(analyzed),
        },
        "sentiment_summary": sentiment_summary,
        "sentiment_by_subreddit": sub_sentiment,
        "keywords": keywords,
        "wordcloud": wordcloud_b64,
        "top_posts": [_serialize_post(p) for p in top_posts],
        "subreddit_distribution": [
            {"subreddit": k, "count": v} for k, v in sub_dist.items()
        ],
        "all_time": {
            "total_posts_ever": all_time_total,
            "sentiment_counts": all_time_counts,
        },
    })


@app.route("/api/history")
def history():
    """Return recent posts saved in the SQLite database."""
    limit = min(int(request.args.get("limit", 50)), 200)
    posts = get_recent_posts(limit=limit)
    return jsonify({"posts": posts, "count": len(posts)})


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/subreddits")
def available_subreddits():
    subs = [
        "technology", "worldnews", "business", "science", "programming",
        "artificial", "MachineLearning", "stocks", "politics", "gaming",
    ]
    return jsonify({"subreddits": subs})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
