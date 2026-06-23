import json
import os
import datetime
import time
import trafilatura
import feedparser
import re # Naya import exact word match ke liye

EXAM_KEYWORDS = [
    # 🏦 Banking, Finance & Economy
    "Quarterly Result", "Fiscal Deficit", "Direct Tax", "GST", "Forex Reserves", 
    "World Bank", "IMF", "RBI", "SEBI", "Repo Rate", "Inflation", "UPI", "NPCI",
    "Fund", "Allocated", "Budget", "Penalty", "Fined", "Acquires", "Merger", 
    "Stake", "Dividend", "Economy", "GDP Growth",
    
    # 🏅 Ranks, Reports & Indices
    "Ranked", "Index", "Rank", "Report", "Position", "Topped",
    
    # 👔 Appointments, Resignations & Obituaries
    "Appointed as", "Takes charge as", "Selected as", "Elected", "Takes over", 
    "Resigns", "Steps down", "Passes away",
    
    # 🤝 Agreements & Partnerships
    "MoU", "Bilateral Agreement", "Signs", "Pact", "Agrees", "Partnered", 
    "Collaborates", "Deal",
    
    # 🚀 Defence, Space & Science
    "DRDO", "ISRO", "Military Exercise", "Naval Exercise", "Air Force", "Missile", 
    "Spacecraft", "Satellite", "Defence Ministry", "Inducted", "Commissioned",
    
    # 🏛️ National, Schemes & Judiciary
    "Yojana", "Scheme", "Cabinet Approval", "Supreme Court", "Election Commission", 
    "Launched", "Unveiled", "Inaugurated", "Approved", "Sanctioned", "Portal", "Initiative",
    
    # 🏆 Awards & Sports
    "Nobel Prize", "Sahitya Akademi", "Awarded", "Honoured", "Host", "Venue", 
    "Medal", "Tournament", "Championship", "Cup", "Trophy", "Grand Slam", "Olympics"
]

RSS_FEEDS = [
    # 🏦 Pure Economy & Business (Most Important for Banking)
    "https://www.livemint.com/rss/news",
    "https://www.business-standard.com/rss/latest-news",
    "https://www.business-standard.com/rss/economy-policy-102.rss", # Economy Specific
    "https://economictimes.indiatimes.com/rssfeeds/1898055.cms", # Wealth/Finance
    "https://economictimes.indiatimes.com/rssfeeds/1373380680.cms", # Economy
    "https://www.thehindubusinessline.com/economy/feeder/default.rss", # Business Line (Top Source)

    # 🏛️ National & Government Policies (Important for SSC/UPSC base)
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://indianexpress.com/section/india/feed/", # Indian Express India section

    # 🚀 Science, Tech & Defence
    "https://www.thehindu.com/sci-tech/science/feeder/default.rss",
    "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",

    # 🏆 Sports (For tournament winners and venues)
    "https://www.thehindu.com/sport/feeder/default.rss",
    "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms", # TOI Sports

    # 📰 Reliable General Outlets
    "https://www.news18.com/rss/india.xml",
    "https://www.ndtv.com/rss/india-news" # NDTV Top Stories
]

HISTORY_FILE = "scraped_urls.json"

def load_history():
    """Pehle se scrape kiye gaye URLs ko load karta hai taki duplicates na aayen."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_history(history_set):
    """Scrape ho chuke URLs ko save karta hai."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history_set), f, indent=4)

def fetch_clean_article(url):
    """Trafilatura ka use karke sirf pure news text nikalta hai."""
    try:
        time.sleep(0.5)
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            return text if text else ""
        return ""
    except Exception as e:
        print(f"⚠️ Error fetching: {url} | Issue: {e}")
        return ""

def is_exam_relevant(title):
    """
    Regex ka use karke exact word boundaries (\b) match karta hai.
    Isse 'MoU', 'famous' me match nahi hoga.
    """
    for keyword in EXAM_KEYWORDS:
        # \b ensures that we match the exact whole word or phrase
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, title, re.IGNORECASE):
            return True
    return False

def run_scraper():
    scraped_history = load_history()
    new_articles = []
    today_date = datetime.date.today().strftime("%Y-%m-%d")

    print("🚀 Scraper Started: Fetching premium exam-oriented news...\n")

    for feed_url in RSS_FEEDS:
        print(f"📡 Scanning Feed: {feed_url}")
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if link in scraped_history:
                continue

            # Naya updated strict checking logic yahan apply kiya hai
            if is_exam_relevant(title):
                clean_content = fetch_clean_article(link)

                if clean_content and len(clean_content) > 200:
                    new_articles.append({
                        "title": title,
                        "content": clean_content,
                        "link": link,
                        "date": today_date,
                    })
                    scraped_history.add(link)
                    print(f"✅ Saved: {title[:60]}...")

    if new_articles:
        with open("1.json", "w", encoding="utf-8") as f:
            json.dump(new_articles, f, indent=4, ensure_ascii=False)
        print(f"✅ {len(new_articles)} naye articles '1.json' me overwrite ho gaye hain.")

        with open("all.txt", "a", encoding="utf-8") as f:
            for article in new_articles:
                f.write(json.dumps(article, ensure_ascii=False) + "\n")
        print(f"✅ Sabhi naye articles 'all.txt' me history ke roop me add ho gaye hain.")

        save_history(scraped_history)
        print("\n🎉 Success! Scraper ka kaam complete ho gaya.")
    else:
        print("\n🤷‍♂️ Koi nayi relevant news nahi mili. Sab up-to-date hai!")

if __name__ == "__main__":
    run_scraper()
