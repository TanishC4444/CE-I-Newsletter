import feedparser
from newspaper import Article
import os
import json
from datetime import datetime
from time import sleep
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from llama_cpp import Llama

# Configuration
MODEL_PATH = os.getenv('MODEL_PATH', './models/mistral-7b-instruct-v0.1.Q4_K_M.gguf')
PROCESSED_URLS_FILE = 'processed_urls.json'
EMAIL_TO = os.getenv('EMAIL_TO', 'tanishchauhan4444@gmail.com')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'tanishchauhan4444@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'sexz mqmo ygov axxp')

# RSS feeds organized by region
FEEDS = {
    "US": {
        "CNN": "http://rss.cnn.com/rss/cnn_topstories.rss",
        "NPR": "https://feeds.npr.org/1001/rss.xml",
        "Washington Post": "https://feeds.washingtonpost.com/rss/national",
        "NY Times US": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
        "ABC Top": "https://feeds.abcnews.com/abcnews/topstories",
    },
    "World": {
        "BBC World": "http://feeds.bbci.co.uk/world/rss.xml",
        "NY World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    },
    "Middle East": {
        "NY Middle East": "https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",
    },
    "Asia": {
        "NY Asia Pacific": "https://rss.nytimes.com/services/xml/rss/nyt/AsiaPacific.xml",
        "CNBC Asia": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19832390",
    },
    "Europe": {
        "NY Europe": "https://rss.nytimes.com/services/xml/rss/nyt/Europe.xml",
        "CNBC EU": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19794221",
    },
    "Africa": {
        "NY Africa": "https://rss.nytimes.com/services/xml/rss/nyt/Africa.xml",
    },
    "Business": {
        "CNBC Business": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
        "NY Business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        "WSJ Business": "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
    },
    "Technology": {
        "NY Tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "CNBC Tech": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
    }
}

# Initialize AI model
print("Loading AI model...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_gpu_layers=-1,
    n_threads=4,
    n_batch=512,
    verbose=False
)

SUMMARY_PROMPT = """Analyze this news article and provide a concise summary in exactly this format:

WHO: [Key people/organizations involved]
WHAT: [What happened]
WHEN: [Time/date if mentioned]
WHERE: [Location]
WHY: [Reason/context if available]

Keep each point to 1-2 sentences maximum. Be specific and factual.

Article: {article}

Summary:"""

def load_processed_urls():
    """Load set of already processed URLs"""
    if os.path.exists(PROCESSED_URLS_FILE):
        with open(PROCESSED_URLS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_urls(urls):
    """Save processed URLs to file"""
    with open(PROCESSED_URLS_FILE, 'w') as f:
        json.dump(list(urls), f)

def collect_articles():
    """Collect new articles from RSS feeds"""
    processed_urls = load_processed_urls()
    new_articles = []
    
    print(f"Loaded {len(processed_urls)} previously processed URLs")
    
    for region, feeds in FEEDS.items():
        print(f"\n📰 Collecting from {region}...")
        
        for feed_name, feed_url in feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Limit per feed
                    url = entry.link
                    
                    if url in processed_urls:
                        continue
                    
                    try:
                        article = Article(url)
                        article.download()
                        article.parse()
                        
                        if len(article.text.split()) > 100:
                            new_articles.append({
                                'region': region,
                                'source': feed_name,
                                'title': entry.title,
                                'url': url,
                                'text': article.text[:3000]  # Limit length
                            })
                            processed_urls.add(url)
                            print(f"  ✅ {feed_name}: {entry.title[:60]}...")
                        
                    except Exception as e:
                        print(f"  ❌ Failed to fetch article: {e}")
                    
                    sleep(0.2)
                    
            except Exception as e:
                print(f"  ❌ Failed to process {feed_name}: {e}")
    
    save_processed_urls(processed_urls)
    print(f"\n✅ Collected {len(new_articles)} new articles")
    return new_articles

def summarize_article(article_text):
    """Use AI to summarize article in WHO/WHAT/WHEN/WHERE/WHY format"""
    try:
        prompt = SUMMARY_PROMPT.format(article=article_text)
        
        response = llm(
            prompt,
            max_tokens=300,
            temperature=0.3,
            top_p=0.9,
            stop=["Article:", "\n\nHere"],
            echo=False
        )
        
        summary = response['choices'][0]['text'].strip()
        
        # Ensure it has the required format
        if 'WHO:' in summary and 'WHAT:' in summary:
            return summary
        else:
            return None
            
    except Exception as e:
        print(f"Error summarizing: {e}")
        return None

def create_html_email(articles_by_region):
    """Create beautiful HTML email with summaries"""
    
    # Color scheme by region
    region_colors = {
        "US": "#1e40af",
        "World": "#059669", 
        "Middle East": "#dc2626",
        "Asia": "#9333ea",
        "Europe": "#0891b2",
        "Africa": "#ea580c",
        "Business": "#065f46",
        "Technology": "#4f46e5"
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #1f2937;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9fafb;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 12px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 16px;
            }}
            .region-section {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 25px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .region-header {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid;
            }}
            .article {{
                margin-bottom: 25px;
                padding-bottom: 25px;
                border-bottom: 1px solid #e5e7eb;
            }}
            .article:last-child {{
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }}
            .article-title {{
                font-size: 18px;
                font-weight: 600;
                color: #111827;
                margin-bottom: 8px;
            }}
            .article-title a {{
                color: #111827;
                text-decoration: none;
            }}
            .article-title a:hover {{
                color: #667eea;
            }}
            .article-source {{
                font-size: 13px;
                color: #6b7280;
                margin-bottom: 12px;
            }}
            .summary {{
                background: #f9fafb;
                padding: 15px;
                border-radius: 8px;
                font-size: 14px;
            }}
            .summary-line {{
                margin: 8px 0;
            }}
            .summary-label {{
                font-weight: 600;
                color: #374151;
            }}
            .footer {{
                text-align: center;
                color: #6b7280;
                font-size: 13px;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📰 Your News Digest</h1>
            <p>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
    """
    
    for region, articles in articles_by_region.items():
        if not articles:
            continue
            
        color = region_colors.get(region, "#6b7280")
        
        html += f"""
        <div class="region-section">
            <div class="region-header" style="border-color: {color}; color: {color};">
                {region} ({len(articles)} articles)
            </div>
        """
        
        for article in articles:
            html += f"""
            <div class="article">
                <div class="article-title">
                    <a href="{article['url']}" target="_blank">{article['title']}</a>
                </div>
                <div class="article-source">📌 {article['source']}</div>
            """
            
            if article.get('summary'):
                html += '<div class="summary">'
                for line in article['summary'].split('\n'):
                    if line.strip() and ':' in line:
                        label, content = line.split(':', 1)
                        html += f'<div class="summary-line"><span class="summary-label">{label.strip()}:</span> {content.strip()}</div>'
                html += '</div>'
            
            html += '</div>'
        
        html += '</div>'
    
    html += """
        <div class="footer">
            <p>Generated automatically every 4 hours • Powered by AI</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(html_content, article_count):
    """Send HTML email via Gmail"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📰 News Digest - {article_count} New Articles - {datetime.now().strftime("%b %d, %Y")}'
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {EMAIL_TO}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def main():
    """Main function to run the digest system"""
    print("=" * 60)
    print(f"🚀 Starting News Digest - {datetime.now()}")
    print("=" * 60)
    
    # Step 1: Collect articles
    articles = collect_articles()
    
    if not articles:
        print("\n📭 No new articles found. Exiting.")
        return
    
    # Step 2: Summarize articles
    print(f"\n🤖 Summarizing {len(articles)} articles with AI...")
    
    for i, article in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] {article['title'][:60]}...")
        summary = summarize_article(article['text'])
        article['summary'] = summary
        if summary:
            print("  ✅ Summarized")
        else:
            print("  ⚠️ Summary failed")
    
    # Step 3: Group by region
    articles_by_region = {}
    for article in articles:
        region = article['region']
        if region not in articles_by_region:
            articles_by_region[region] = []
        articles_by_region[region].append(article)
    
    # Step 4: Create and send email
    print(f"\n📧 Creating email...")
    html = create_html_email(articles_by_region)
    
    print(f"📤 Sending email...")
    send_email(html, len(articles))
    
    print(f"\n✅ Complete! Processed {len(articles)} articles")
    print("=" * 60)

if __name__ == "__main__":
    main()