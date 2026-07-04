"""
news_scraper.py
Fetches live news headlines from NewsAPI.org.
Falls back to mock data when the API key is not configured or a request fails.
"""

import os
import re
import random
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# Map our "subreddit-style" categories to NewsAPI's supported categories
CATEGORY_MAP = {
    "technology": "technology",
    "worldnews": "general",
    "business": "business",
    "science": "science",
    "programming": "science",  # NewsAPI has no "programming" category
}
# ---------------------------------------------------------------------------
# Mock data – used when no API key is provided or the request fails
# ---------------------------------------------------------------------------
MOCK_POSTS = [
    {"title": "GPT-5 rumored to launch with real-time web browsing built in", "score": 0, "comments": 0, "subreddit": "technology", "url": "https://example.com", "created_utc": datetime.now() - timedelta(hours=2), "text": "OpenAI is reportedly planning to release GPT-5 with native web browsing and multimodal capabilities."},
    {"title": "Electric vehicles now outsell petrol cars in 12 countries", "score": 0, "comments": 0, "subreddit": "worldnews", "url": "https://example.com", "created_utc": datetime.now() - timedelta(hours=3), "text": "A new report shows EV adoption has crossed the tipping point in a dozen nations."},
    {"title": "Global markets rally as inflation data beats expectations", "score": 0, "comments": 0, "subreddit": "business", "url": "https://example.com", "created_utc": datetime.now() - timedelta(hours=6), "text": "Stock markets surged today after inflation figures came in lower than analysts predicted."},
    {"title": "Quantum computing achieves 1 million qubit milestone", "score": 0, "comments": 0, "subreddit": "science", "url": "https://example.com", "created_utc": datetime.now() - timedelta(hours=4), "text": "A new quantum processor reaches one million qubits, a major computing milestone."},
]


def _fetch_category(category: str, page_size: int) -> list[dict]:
    """Fetch top headlines for a single NewsAPI category."""
    news_category = CATEGORY_MAP.get(category, "general")
    params = {
        "category": news_category,
        "language": "en",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }
    resp = requests.get(NEWS_API_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    posts = []
    for article in data.get("articles", []):
        title = article.get("title") or ""
        if not title or title == "[Removed]":
            continue
        posts.append({
            "title": title,
            "score": 0,
            "comments": 0,
            "subreddit": category,  # keep original key name for compatibility
            "url": article.get("url", ""),
            "created_utc": article.get("publishedAt", ""),
            "text": (article.get("description") or "")[:500],
        })
    return posts


def fetch_trending_posts(subreddits: list[str], limit: int = 50) -> list[dict]:
    """
    Fetch top headlines across the given categories from NewsAPI.
    Falls back to mock data if the API key is missing or requests fail.
    """
    if not NEWS_API_KEY:
        pool = [p for p in MOCK_POSTS if p["subreddit"] in subreddits] or MOCK_POSTS
        random.shuffle(pool)
        return pool[:limit]

    posts = []
    per_category = max(1, limit // max(1, len(subreddits)))

    for category in subreddits:
        try:
            posts.extend(_fetch_category(category, per_category))
        except Exception:
            continue

    return posts if posts else MOCK_POSTS[:limit]


def extract_keywords(posts: list[dict], top_n: int = 20) -> list[dict]:
    """Extract and count significant keywords from post titles."""
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "has", "have", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "not", "no", "as", "it",
        "its", "this", "that", "these", "those", "i", "you", "he", "she",
        "we", "they", "what", "which", "who", "how", "when", "where", "why",
        "all", "any", "both", "each", "more", "most", "other", "some", "such",
        "than", "then", "there", "so", "up", "out", "about", "after", "if",
        "new", "just", "now", "over", "s", "t", "re", "ve", "d",
    }

    freq: dict[str, int] = {}
    for post in posts:
        words = re.findall(r"[a-zA-Z]{3,}", post["title"].lower())
        for w in words:
            if w not in STOPWORDS:
                freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [{"word": w, "count": c} for w, c in sorted_words[:top_n]]