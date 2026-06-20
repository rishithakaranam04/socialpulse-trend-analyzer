# 📊 SocialPulse — Reddit Trend & Sentiment Analyzer

A real-time dashboard that fetches trending Reddit posts, analyzes sentiment using VADER NLP, stores results in SQLite, and visualizes everything with Chart.js.

This is the **simplified stack** version: Flask + SQLite + PRAW + VADER (TextBlob removed) + Chart.js. See `SocialPulse_Complete_Placement_Guide.docx` for the full beginner-friendly build guide, interview prep, and day-by-day plan.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite |
| Reddit Data | PRAW |
| Sentiment Analysis | VADER (only) |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Deployment | GitHub + Render |

---

## Folder Structure

```
socialpulse/
├── app.py                    # Flask app + all routes
├── requirements.txt
├── Procfile                  # Gunicorn start command (Render)
├── render.yaml                # One-click Render deploy config
├── .env.example
├── .gitignore
│
├── utils/
│   ├── reddit_scraper.py     # PRAW fetcher + mock-data fallback
│   ├── sentiment_analyzer.py # VADER-only sentiment pipeline
│   └── wordcloud_gen.py      # Word cloud PNG generator (base64)
│
├── database/
│   └── db.py                 # SQLite connection, schema, queries
│
├── templates/
│   └── index.html            # Dashboard (HTML + CSS + JS + Chart.js)
│
├── static/
│   ├── css/
│   └── js/
│
└── tests/
    └── test_core.py          # 13 unit tests (sentiment, keywords, database)
```

---

## Quick Start

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
cp .env.example .env           # optional — works with mock data without this

python app.py
```

Open **http://localhost:5000**

---

## Reddit API Setup (Optional)

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app" → type: **script**
3. Copy `client_id` and `client_secret` into `.env`

Without credentials, the app automatically uses realistic mock data.

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard page |
| `GET /api/analyze?subreddits=...&limit=...` | Fetch, analyze, save, return JSON |
| `GET /api/history?limit=...` | Recent posts from SQLite |
| `GET /api/health` | Health check |
| `GET /api/subreddits` | List of supported subreddits |

---

## Running Tests

```bash
python tests/test_core.py
```

Expected: **13 passed, 0 failed**

---

## Deployment (Render — Free)

1. Push to GitHub
2. Create a new Web Service on render.com, connect your repo
3. Render reads `render.yaml` automatically
4. Add `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` as environment variables
5. Deploy → get your live URL

---

## License

MIT — free for academic and personal use.
