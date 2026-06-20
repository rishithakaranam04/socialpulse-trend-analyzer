"""
sentiment_analyzer.py
Sentiment analysis using ONLY VADER (Valence Aware Dictionary and sEntiment Reasoner).
TextBlob has been intentionally removed to keep the dependency list minimal.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load the analyzer once at import time and reuse it for every post.
# Creating a new SentimentIntensityAnalyzer for every post would be slow.
_vader = SentimentIntensityAnalyzer()


def analyze_post(post: dict) -> dict:
    """
    Run VADER sentiment analysis on a single post's title + text.

    VADER returns 4 scores:
      pos, neg, neu  -> proportions of the text (always sum to 1.0)
      compound       -> a single normalized score from -1.0 to +1.0

    Classification thresholds (from the original VADER research paper):
      compound >= 0.05   -> positive
      compound <= -0.05  -> negative
      otherwise          -> neutral
    """
    content = f"{post.get('title', '')} {post.get('text', '')}".strip()

    scores = _vader.polarity_scores(content)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {
        **post,
        "sentiment_label": label,
        "sentiment_score": round(compound, 3),
        "sentiment_pos": round(scores["pos"], 3),
        "sentiment_neg": round(scores["neg"], 3),
        "sentiment_neu": round(scores["neu"], 3),
    }


def analyze_all(posts: list[dict]) -> list[dict]:
    """Run sentiment analysis on a list of posts."""
    return [analyze_post(p) for p in posts]


def aggregate_sentiment(analyzed_posts: list[dict]) -> dict:
    """
    Compute dashboard-level sentiment summary: counts, percentages, average score.
    """
    if not analyzed_posts:
        return {
            "positive": 0, "negative": 0, "neutral": 0,
            "positive_pct": 0, "negative_pct": 0, "neutral_pct": 0,
            "avg_score": 0.0, "total": 0,
        }

    counts = {"positive": 0, "negative": 0, "neutral": 0}
    total_score = 0.0

    for p in analyzed_posts:
        counts[p["sentiment_label"]] += 1
        total_score += p["sentiment_score"]

    total = len(analyzed_posts)
    return {
        "positive": counts["positive"],
        "negative": counts["negative"],
        "neutral": counts["neutral"],
        "positive_pct": round(counts["positive"] / total * 100, 1),
        "negative_pct": round(counts["negative"] / total * 100, 1),
        "neutral_pct": round(counts["neutral"] / total * 100, 1),
        "avg_score": round(total_score / total, 3),
        "total": total,
    }


def sentiment_by_subreddit(analyzed_posts: list[dict]) -> list[dict]:
    """Group average sentiment score by subreddit, for the comparison bar chart."""
    groups: dict[str, list[float]] = {}
    for p in analyzed_posts:
        sub = p["subreddit"]
        groups.setdefault(sub, []).append(p["sentiment_score"])

    result = []
    for sub, scores in groups.items():
        avg = round(sum(scores) / len(scores), 3)
        result.append({"subreddit": sub, "avg_sentiment": avg, "post_count": len(scores)})

    return sorted(result, key=lambda x: x["avg_sentiment"], reverse=True)


# ── Standalone test runner ──────────────────────────────────────────────────
# Run this file directly to verify VADER is working correctly:
#     python utils/sentiment_analyzer.py
if __name__ == "__main__":
    sample_posts = [
        {"title": "Amazing new AI discovery could cure diseases!", "text": "Wonderful results in clinical trials."},
        {"title": "Scientists publish new findings on climate data", "text": "Revenue figures are as follows."},
        {"title": "Company lays off thousands of workers, market crashes", "text": "Devastating impact on communities."},
        {"title": "TERRIBLE service, never using this again!!!", "text": ""},
    ]

    print("Testing VADER sentiment analysis:\n")
    for post in sample_posts:
        result = analyze_post(post)
        print(f"  '{result['title']}'")
        print(f"    -> {result['sentiment_label']} (compound: {result['sentiment_score']})\n")
