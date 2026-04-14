# UCLA Mindful RSS Feed Server

A tiny Flask app that scrapes the UCLA Mindful weekly meditations page live and serves a valid podcast RSS feed — compatible with Apple Podcasts, Overcast, Pocket Casts, Castro, and any other standard podcast app.

Every time a podcast app fetches the feed URL, it gets a freshly scraped list of episodes.

---

## Deploy for free on Render (recommended, ~2 minutes)

1. Push this folder to a GitHub repo (public or private)
2. Go to https://render.com and create a free account
3. Click **New → Web Service** and connect your repo
4. Set these values:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance type:** Free
5. Click **Deploy**

Your feed will be live at:
```
https://your-app-name.onrender.com/feed.xml
```

Paste that URL into any podcast app's "Add by URL" option.

---

## Deploy on Railway

1. Push to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub repo
3. Railway auto-detects the Procfile — just deploy
4. Your URL will be something like `https://your-app.up.railway.app/feed.xml`

---

## Run locally (for testing)

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:8000/feed.xml in your browser or point a local podcast app at it.

---

## How it works

- `GET /feed.xml` — scrapes the UCLA Mindful page, parses the episode table, returns RSS XML
- `GET /` — simple landing page with a link to the feed
- Episodes are sorted newest-first
- Handles `.mp3`, `.m4a`, and `.wav` audio formats
- Feed updates automatically whenever UCLA posts a new episode — no manual steps needed
