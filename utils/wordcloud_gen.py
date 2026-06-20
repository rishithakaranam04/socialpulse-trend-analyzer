"""
wordcloud_gen.py
Generates a word-cloud PNG (base64-encoded) from post titles.
"""

import io
import base64
import re
from wordcloud import WordCloud, STOPWORDS


_EXTRA_STOPS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "will", "new",
    "just", "now", "more", "first", "after", "over", "up", "out", "so",
    "its", "this", "that", "about", "as", "it", "has", "have", "had",
    "be", "been", "does", "did", "can", "could", "s", "t", "re", "ve",
}
STOPS = STOPWORDS.union(_EXTRA_STOPS)


def generate_wordcloud_base64(posts: list[dict], width: int = 900, height: int = 450) -> str:
    """
    Build a word cloud from post titles and return a base64-encoded PNG string
    suitable for embedding directly in an <img src="data:image/png;base64,..."> tag.
    """
    text = " ".join(
        re.sub(r"[^a-zA-Z\s]", " ", post.get("title", ""))
        for post in posts
    )

    if not text.strip():
        return ""

    wc = WordCloud(
        width=width,
        height=height,
        background_color="#0f172a",   # dark navy — matches dashboard theme
        stopwords=STOPS,
        colormap="cool",
        max_words=80,
        min_font_size=11,
        max_font_size=90,
        prefer_horizontal=0.75,
        collocations=False,
        relative_scaling=0.55,
    ).generate(text)

    buf = io.BytesIO()
    wc.to_image().save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
