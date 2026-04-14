import re
from datetime import datetime, timezone
from flask import Flask, Response
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

FEED_URL = "https://www.uclahealth.org/uclamindful/weekly-meditations-talks"
BASE_URL = "https://d1cy5zxxhbcbkk.cloudfront.net/hammer-podcast/"

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 2, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "march": 3, "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12, "january": 1,
    "february": 2, "april": 4
}

def parse_date(raw):
    raw = raw.strip().rstrip(".")
    # normalize: "Apr. 2, 2026" / "April 2, 2026" / "Aug. 28, 2025"
    raw = re.sub(r"\.", "", raw)
    parts = raw.replace(",", "").split()
    if len(parts) < 3:
        return None
    month_str = parts[0].lower()
    month = MONTH_MAP.get(month_str)
    if not month:
        return None
    try:
        day = int(parts[1])
        year = int(parts[2])
        return datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None

def rfc2822(dt):
    if not dt:
        return ""
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

def escape_xml(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))

def guess_mime(url):
    url = url.lower()
    if url.endswith(".m4a"):
        return "audio/x-m4a"
    if url.endswith(".wav"):
        return "audio/wav"
    return "audio/mpeg"

def fetch_episodes():
    resp = requests.get(FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    episodes = []
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            date_raw = cells[0].get_text(strip=True)
            topic = cells[1].get_text(strip=True)
            instructor = cells[2].get_text(strip=True)
            link_tag = cells[3].find("a", href=True)
            if not link_tag:
                continue
            audio_url = link_tag["href"]
            if not audio_url.startswith("http"):
                continue
            dt = parse_date(date_raw)
            episodes.append({
                "date_raw": date_raw,
                "dt": dt,
                "topic": topic,
                "instructor": instructor,
                "audio_url": audio_url,
            })

    episodes.sort(key=lambda e: e["dt"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return episodes

def build_rss(episodes):
    items = []
    for ep in episodes:
        title = ep["topic"] or "UCLA Mindful Session"
        if ep["instructor"]:
            title = f"{title} – {ep['instructor']}"
        description = f"{ep['topic']} with {ep['instructor']}. Recorded {ep['date_raw']}."
        items.append(f"""
    <item>
      <title>{escape_xml(title)}</title>
      <pubDate>{rfc2822(ep['dt'])}</pubDate>
      <description>{escape_xml(description)}</description>
      <enclosure url="{escape_xml(ep['audio_url'])}" type="{guess_mime(ep['audio_url'])}" length="0"/>
      <guid isPermaLink="false">{escape_xml(ep['audio_url'])}</guid>
      <itunes:author>{escape_xml(ep['instructor'])}</itunes:author>
      <itunes:summary>{escape_xml(description)}</itunes:summary>
    </item>""")

    now = rfc2822(datetime.now(tz=timezone.utc))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>UCLA Mindful – Weekly Meditations &amp; Talks</title>
    <link>{FEED_URL}</link>
    <description>Weekly meditations and talks from UCLA Mindful, led by Diana Winston, Marvin G. Belzer, Allyson Pimentel, and guest teachers.</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{{SELF_URL}}" rel="self" type="application/rss+xml"/>
    <itunes:author>UCLA Mindful</itunes:author>
    <itunes:category text="Health &amp; Fitness">
      <itunes:category text="Mental Health"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="https://www.uclahealth.org/sites/default/files/styles/max_650x650/public/2022-04/uclamindful_900x900.jpg"/>
    {"".join(items)}
  </channel>
</rss>"""

@app.route("/feed.xml")
def feed():
    try:
        episodes = fetch_episodes()
        xml = build_rss(episodes)
        return Response(xml, mimetype="application/rss+xml")
    except Exception as e:
        return Response(f"Error generating feed: {e}", status=500, mimetype="text/plain")

@app.route("/")
def index():
    return Response(
        "<h2>UCLA Mindful RSS Feed</h2>"
        "<p>Subscribe to <a href='/feed.xml'>/feed.xml</a> in any podcast app.</p>",
        mimetype="text/html"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
