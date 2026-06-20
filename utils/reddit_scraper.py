"""
reddit_scraper.py
Fetches posts from Reddit using PRAW (Python Reddit API Wrapper).
Falls back to mock data when credentials are not configured.
"""

import os
import re
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Mock data – used when no Reddit credentials are provided
# ---------------------------------------------------------------------------
MOCK_POSTS = [
    {"title": "GPT-5 rumored to launch with real-time web browsing built in", "score": 45230, "comments": 3812, "subreddit": "technology", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=2), "text": "OpenAI is reportedly planning to release GPT-5 with native web browsing and multimodal capabilities far beyond current models."},
    {"title": "Meta releases open-source AI model beating proprietary systems", "score": 38910, "comments": 2944, "subreddit": "technology", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=5), "text": "Meta's latest Llama model outperforms several closed-source competitors on major benchmarks according to independent evaluations."},
    {"title": "Python 3.14 performance improvements are insane – 50% faster", "score": 29400, "comments": 1870, "subreddit": "programming", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=8), "text": "The upcoming Python 3.14 release includes significant JIT compiler improvements that result in dramatic performance gains."},
    {"title": "Electric vehicles now outsell petrol cars in 12 countries", "score": 22100, "comments": 4210, "subreddit": "worldnews", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=3), "text": "A new report shows EV adoption has crossed the tipping point in a dozen nations, signaling a major market shift."},
    {"title": "AI-powered drug discovery cuts development time by 70%", "score": 19800, "comments": 987, "subreddit": "science", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=12), "text": "Researchers used deep learning to identify viable drug candidates 10x faster than traditional methods in a landmark study."},
    {"title": "Remote work productivity studies show 23% increase in output", "score": 17500, "comments": 5600, "subreddit": "business", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=6), "text": "A Stanford meta-analysis of 200 remote-work studies concludes that flexible workers consistently outperform office counterparts."},
    {"title": "Rust overtakes C++ in new systems projects for the first time", "score": 15700, "comments": 2300, "subreddit": "programming", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=10), "text": "GitHub's annual developer survey reveals Rust is now the preferred language for new systems-level software."},
    {"title": "Climate report: 2025 was the hottest year on record by wide margin", "score": 41200, "comments": 6800, "subreddit": "worldnews", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=1), "text": "NASA and NOAA jointly confirmed 2025 shattered previous temperature records, with ocean heat content at all-time high."},
    {"title": "SpaceX Starship completes first crewed Mars flyby mission", "score": 88000, "comments": 12400, "subreddit": "science", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(minutes=45), "text": "In a historic milestone, SpaceX's Starship with a crew of 4 completed a successful Mars flyby and is returning to Earth."},
    {"title": "New battery technology offers 1000km range on single charge", "score": 33400, "comments": 4100, "subreddit": "technology", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=7), "text": "A breakthrough solid-state battery announced by Toyota promises 1000km range, 10-minute recharge, and 20-year lifespan."},
    {"title": "Quantum computing achieves 1 million qubit milestone", "score": 55000, "comments": 3200, "subreddit": "science", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=4), "text": "IBM's new quantum processor reaches one million qubits, a threshold scientists say unlocks practical quantum advantage."},
    {"title": "Global chip shortage ends as TSMC opens 3 new fabs", "score": 12300, "comments": 890, "subreddit": "business", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=14), "text": "After three years of shortages, semiconductor supply finally exceeds demand as Taiwan, US, and Japan fabs come online."},
    {"title": "React 20 drops virtual DOM – blazing fast rendering", "score": 28900, "comments": 3400, "subreddit": "programming", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=9), "text": "The React team's complete rewrite eliminates the virtual DOM bottleneck, yielding 5x faster renders on complex UIs."},
    {"title": "WHO declares end to antibiotic resistance crisis with new drug class", "score": 67000, "comments": 7800, "subreddit": "worldnews", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=11), "text": "A new class of antibiotics effective against all drug-resistant superbugs has been approved after fast-track trials."},
    {"title": "Google DeepMind solves protein folding for entire human proteome", "score": 49000, "comments": 4500, "subreddit": "science", "url": "https://reddit.com", "created_utc": datetime.now() - timedelta(hours=16), "text": "DeepMind's AlphaFold 3 has now mapped every human protein structure, opening doors to personalized medicine at scale."},
]


def _try_reddit_client():
    """Attempt to create an authenticated PRAW Reddit client."""
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent = os.getenv("REDDIT_USER_AGENT", "SocialTrendAnalyzer/1.0")

    if not client_id or client_id == "your_client_id_here":
        return None

    try:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        # Lightweight auth check
        reddit.user.me()
        return reddit
    except Exception:
        return None


def fetch_trending_posts(subreddits: list[str], limit: int = 50) -> list[dict]:
    """
    Fetch hot posts from the given subreddits.
    Returns a list of post dicts. Falls back to mock data if API is unavailable.
    """
    reddit = _try_reddit_client()

    if reddit is None:
        # Return shuffled mock data filtered by requested subreddits
        pool = [p for p in MOCK_POSTS if p["subreddit"] in subreddits] or MOCK_POSTS
        random.shuffle(pool)
        return pool[:limit]

    posts = []
    per_sub = max(1, limit // len(subreddits))

    for sub_name in subreddits:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.hot(limit=per_sub):
                if post.stickied:
                    continue
                posts.append({
                    "title": post.title,
                    "score": post.score,
                    "comments": post.num_comments,
                    "subreddit": sub_name,
                    "url": f"https://reddit.com{post.permalink}",
                    "created_utc": datetime.utcfromtimestamp(post.created_utc),
                    "text": (post.selftext or "")[:500],
                })
        except Exception:
            continue

    return posts if posts else MOCK_POSTS[:limit]


def extract_keywords(posts: list[dict], top_n: int = 20) -> list[dict]:
    """
    Extract and count significant keywords from post titles.
    Returns list of {word, count} dicts sorted by frequency descending.
    """
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
