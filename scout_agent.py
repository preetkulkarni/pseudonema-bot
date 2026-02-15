import os
import feedparser
import asyncio
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

async def run_scout(topic: str):
    print(f"🕵️ Scout starting for: {topic}")

    session_data = {"topic": topic, "status": "scouting"}
    response = supabase.table("research_sessions").insert(session_data).execute()
    session_id = response.data[0]['id']

    collected_items = []

    # --- SOURCE 1: NEWS RSS ---
    news_feeds = [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://news.ycombinator.com/rss",
        "https://www.wired.com/feed/category/security/latest/rss"
    ]

    # --- SOURCE 2: REDDIT RSS ---
    reddit_feeds = [
        f"https://www.reddit.com/r/technology/search.rss?q={topic}&restrict_sr=1&sort=top&t=week",
        f"https://www.reddit.com/r/artificial/search.rss?q={topic}&restrict_sr=1&sort=top&t=week",
        f"https://www.reddit.com/r/programming/search.rss?q={topic}&restrict_sr=1&sort=top&t=week"
    ]

    all_feeds = news_feeds + reddit_feeds

    print(f"📡 Scanning {len(all_feeds)} feeds...")
    
    for feed_url in all_feeds:
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:3]:
                collected_items.append({
                    "session_id": session_id,
                    "source": "Reddit" if "reddit.com" in feed_url else "News",
                    "title": entry.title,
                    "url": entry.link,
                    "summary": entry.summary[:500] if hasattr(entry, 'summary') else ""
                })
        except Exception as e:
            print(f"⚠️ Error parsing {feed_url}: {e}")

    if collected_items:
        print(f"💾 Saving {len(collected_items)} items...")
        supabase.table("raw_news").insert(collected_items).execute()
    
    return len(collected_items), session_id