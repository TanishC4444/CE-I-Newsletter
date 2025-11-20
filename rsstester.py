import requests
import feedparser

FEEDS = {
    "Politics": {
        "The Hill Politics": "https://thehill.com/homenews/administration/feed/",
        "NPR Politics": "https://feeds.npr.org/1014/rss.xml",
        "CNN Politics": "http://rss.cnn.com/rss/cnn_allpolitics.rss",
    },
    "Business & Economy": {
        "Wall Street Journal": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
        "Financial Times": "https://www.ft.com/?format=rss",
        "CNBC Business": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
        "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
    },
    "Health & Medicine": {
        "NPR Health": "https://feeds.npr.org/1128/rss.xml",
        "ScienceDaily Health": "https://www.sciencedaily.com/rss/health_medicine.xml",
    },
    "Environment & Climate": {
        "The Guardian Environment": "https://www.theguardian.com/environment/rss",
        "Inside Climate News": "https://insideclimatenews.org/feed/",
    },
    "Technology": {
        "TechCrunch": "https://techcrunch.com/feed/",
        "MIT Technology Review": "https://www.technologyreview.com/feed/",
    },
    "Science": {
        "Science Daily": "https://www.sciencedaily.com/rss/all.xml",
        "Nature News": "http://feeds.nature.com/nature/rss/current",
        "Scientific American": "http://rss.sciam.com/ScientificAmerican-Global",
        "Phys.org": "https://phys.org/rss-feed/",
    }
}

def check_feed(url):
    try:
        resp = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        status = resp.status_code
        if status != 200:
            return f"❌ HTTP {status}"

        parsed = feedparser.parse(resp.text)
        if parsed.bozo:
            return "❌ Not valid RSS (parse error)"

        # Optional: require at least one entry
        if not parsed.entries:
            return "⚠️ RSS valid but no entries"

        return "✅ VALID RSS FEED"

    except requests.exceptions.RequestException as e:
        return f"❌ Request failed ({e})"


# Run all checks
for category, feeds in FEEDS.items():
    print(f"\n=== {category} ===")
    for name, url in feeds.items():
        result = check_feed(url)
        print(f"{name}: {result}")
