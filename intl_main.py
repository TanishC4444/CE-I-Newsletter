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
MODEL_PATH = './models/mistral-7b-instruct-v0.1.Q4_K_M.gguf'
PROCESSED_URLS_FILE = 'intl_processed_urls.json'

# Email Configuration
EMAIL_RECIPIENTS = [
    "tanishc4444@gmail.com",
    "lakshith.toguta@gmail.com",
    "patildhruv97@gmail.com",
    "emilyzhang8849@gmail.com"
]
EMAIL_FROM = "tanishchauhan4444@gmail.com"
EMAIL_PASSWORD = "sexz mqmo ygov axxp"

# International RSS feeds
FEEDS = {
    "World News": {
        "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "The Guardian International": "https://www.theguardian.com/world/rss",
        "AP World News": "https://apnews.com/apf-topnews",
        "ABC Intl Headlines": "https://feeds.abcnews.com/abcnews/internationalheadlines",            "CNBC World News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "CNBC World News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362", 
        "CNN": "http://rss.cnn.com/rss/cnn_world.rss"
    },
    "Europe": {
        "BBC Europe": "http://feeds.bbci.co.uk/news/world/europe/rss.xml",
        "France 24": "https://www.france24.com/en/europe/rss",
        "Deutsche Welle": "https://rss.dw.com/rdf/rss-en-eu",
    },
    "Asia": {
        "BBC Asia": "http://feeds.bbci.co.uk/news/world/asia/rss.xml",
        "The Diplomat": "https://thediplomat.com/feed/",
        "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar",
    },
    "Middle East": {
        "BBC Middle East": "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "Middle East Monitor": "https://middleeastmnt.disqus.com/latest.rss",
        "Middle East Eye": "https://www.middleeasteye.net/rss"
    },
    "Africa": {
        "BBC Africa": "http://feeds.bbci.co.uk/news/world/africa/rss.xml",
        "France 24": "https://www.france24.com/en/africa/rss"
    },
    "Latin America": {
        "BBC Latin America": "http://feeds.bbci.co.uk/news/world/latin_america/rss.xml",
        " Latin America Affairs RSS Feed": "http://latinamericanaffairs.blogspot.com/feeds/posts/default?alt=rss"     }
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

SUMMARY_PROMPT = """Analyze this international news article and provide a concise summary in exactly this format:

WHO: [Key people/organizations/countries involved]
WHAT: [What happened]
WHEN: [Time/date if mentioned]
WHERE: [Specific location/country/region]
WHY: [Reason/context if available]
GLOBAL IMPACT: [International implications or significance]

Keep each point to 1-2 sentences maximum. Be specific and factual.

Article: {article}

Summary:"""

QUIZ_PROMPT = """Based on the international news articles provided, create 5 multiple choice questions to test comprehension.

STRICT REQUIREMENTS:
- Create exactly 5 questions covering different international articles
- Each question must have exactly 4 options (A, B, C, D)
- Each question must have exactly 1 correct answer
- Questions should test factual recall from the articles
- Include a mix of WHO, WHAT, WHEN, WHERE, WHY questions
- Focus on international/global content

FORMAT (follow exactly):
Q1. [Question about international article content]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]
Correct Answer: [Single letter: A, B, C, or D]

Q2. [Question about international article content]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]
Correct Answer: [Single letter: A, B, C, or D]

[Continue for Q3, Q4, Q5...]

International Articles Summary:
{articles_summary}

Generate exactly 5 questions now:"""

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
    """Collect new international articles from RSS feeds"""
    processed_urls = load_processed_urls()
    new_articles = []
    skipped_count = 0
    
    print(f"Loaded {len(processed_urls)} previously processed URLs")
    
    for region, feeds in FEEDS.items():
        print(f"\n🌍 Collecting from {region}...")
        
        for feed_name, feed_url in feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:
                    url = entry.link
                    
                    if url in processed_urls:
                        continue
                    
                    try:
                        article = Article(url)
                        article.download()
                        article.parse()
                        
                        word_count = len(article.text.split())
                        
                        if word_count < 100:
                            print(f"  ⏭️  Skipped (too short: {word_count} words): {entry.title[:50]}...")
                            skipped_count += 1
                            processed_urls.add(url)
                            continue
                        
                        if len(article.text.strip()) < 200:
                            print(f"  ⏭️  Skipped (minimal content): {entry.title[:50]}...")
                            skipped_count += 1
                            processed_urls.add(url)
                            continue
                        
                        new_articles.append({
                            'region': region,
                            'source': feed_name,
                            'title': entry.title,
                            'url': url,
                            'text': article.text[:3000]
                        })
                        processed_urls.add(url)
                        print(f"  ✅ {feed_name}: {entry.title[:60]}... ({word_count} words)")
                        
                    except Exception as e:
                        print(f"  ❌ Failed to fetch article: {e}")
                    
                    sleep(0.2)
                    
            except Exception as e:
                print(f"  ❌ Failed to process {feed_name}: {e}")
    
    save_processed_urls(processed_urls)
    print(f"\n✅ Collected {len(new_articles)} new international articles (skipped {skipped_count} short/empty articles)")
    return new_articles

def summarize_article(article_text):
    """Use AI to summarize article in WHO/WHAT/WHEN/WHERE/WHY format"""
    try:
        prompt = SUMMARY_PROMPT.format(article=article_text)
        
        response = llm(
            prompt,
            max_tokens=350,
            temperature=0.3,
            top_p=0.9,
            stop=["Article:", "\n\nHere"],
            echo=False
        )
        
        summary = response['choices'][0]['text'].strip()
        
        if 'WHO:' in summary and 'WHAT:' in summary:
            return summary
        else:
            return None
            
    except Exception as e:
        print(f"Error summarizing: {e}")
        return None

def generate_quiz(articles_by_region):
    """Generate quiz questions based on all international articles"""
    try:
        articles_summary = ""
        for region, articles in articles_by_region.items():
            for article in articles:
                if article.get('summary'):
                    articles_summary += f"\nArticle: {article['title']}\n{article['summary']}\n"
        
        articles_summary = articles_summary[:4000]
        
        prompt = QUIZ_PROMPT.format(articles_summary=articles_summary)
        
        response = llm(
            prompt,
            max_tokens=500,
            temperature=0.3,
            top_p=0.9,
            stop=["Articles Summary:", "\n\nHere"],
            echo=False
        )
        
        quiz_text = response['choices'][0]['text'].strip()
        
        questions = []
        current_q = {}
        
        for line in quiz_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Q') and '.' in line:
                if current_q:
                    questions.append(current_q)
                current_q = {'question': line, 'options': [], 'answer': ''}
            elif line.startswith(('A.', 'B.', 'C.', 'D.')):
                if current_q:
                    current_q['options'].append(line)
            elif line.startswith('Correct Answer:'):
                if current_q:
                    current_q['answer'] = line.split(':')[1].strip()
        
        if current_q:
            questions.append(current_q)
        
        return questions
        
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return []

def create_html_email(articles_by_region, quiz_questions):
    """Create beautiful HTML email with international summaries and quiz"""
    
    region_colors = {
        "World News": "#2563eb",
        "Europe": "#0891b2",
        "Asia": "#9333ea",
        "Middle East": "#dc2626",
        "Africa": "#ea580c",
        "Latin America": "#059669"
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
                background: linear-gradient(135deg, #2563eb 0%, #0891b2 100%);
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
                color: #2563eb;
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
            .quiz-section {{
                background: linear-gradient(135deg, #2563eb 0%, #9333ea 100%);
                border-radius: 12px;
                padding: 30px;
                margin-top: 40px;
                margin-bottom: 30px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            .quiz-header {{
                font-size: 28px;
                font-weight: bold;
                color: white;
                text-align: center;
                margin-bottom: 10px;
            }}
            .quiz-subtitle {{
                font-size: 16px;
                color: rgba(255,255,255,0.9);
                text-align: center;
                margin-bottom: 25px;
            }}
            .quiz-question {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            }}
            .question-text {{
                font-size: 17px;
                font-weight: 600;
                color: #111827;
                margin-bottom: 15px;
                line-height: 1.5;
            }}
            .option {{
                background: #f9fafb;
                padding: 12px 15px;
                margin: 8px 0;
                border-radius: 6px;
                font-size: 15px;
                border-left: 3px solid #e5e7eb;
                transition: all 0.2s;
            }}
            .answer {{
                background: #dcfce7;
                padding: 12px 15px;
                margin-top: 12px;
                border-radius: 6px;
                border-left: 3px solid #22c55e;
                font-size: 14px;
                font-weight: 600;
                color: #166534;
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
            <h1>🌍 International News Digest</h1>
            <p>{datetime.now().strftime('%B %d, %Y at %I:%M %p')} UTC</p>
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
    
    if quiz_questions:
        html += """
        <div class="quiz-section">
            <div class="quiz-header">🎯 Test Your Global Knowledge!</div>
            <div class="quiz-subtitle">How well do you know what's happening around the world?</div>
        """
        
        for i, q in enumerate(quiz_questions, 1):
            html += f"""
            <div class="quiz-question">
                <div class="question-text">{q['question']}</div>
            """
            
            for option in q['options']:
                html += f'<div class="option">{option}</div>'
            
            if q.get('answer'):
                html += f'<div class="answer">✅ Correct Answer: {q["answer"]}</div>'
            
            html += '</div>'
        
        html += '</div>'
    
    html += """
        <div class="footer">
            <p>🌍 Your automated international news digest • Powered by AI</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(html_content, article_count):
    """Send HTML email via Gmail to multiple recipients"""
    success_count = 0
    
    for recipient in EMAIL_RECIPIENTS:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'🌍 International News Digest - {article_count} New Articles - {datetime.now().strftime("%b %d, %Y")}'
            msg['From'] = EMAIL_FROM
            msg['To'] = recipient
            
            plain_text = f"International News Digest - {article_count} New Articles\n\nPlease view this email in an HTML-compatible email client."
            text_part = MIMEText(plain_text, 'plain')
            msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(EMAIL_FROM, EMAIL_PASSWORD)
                server.sendmail(EMAIL_FROM, recipient, msg.as_string())
            
            print(f"✅ Email sent successfully to {recipient}")
            success_count += 1
            sleep(1)
            
        except Exception as e:
            print(f"❌ Failed to send email to {recipient}: {e}")
    
    print(f"\n📧 Sent to {success_count}/{len(EMAIL_RECIPIENTS)} recipients")
    return success_count > 0

def main():
    """Main function to run the international digest system"""
    print("=" * 60)
    print(f"🌍 Starting International News Digest - {datetime.now()}")
    print("=" * 60)
    
    articles = collect_articles()
    
    if not articles:
        print("\n📭 No new international articles found. Exiting.")
        return
    
    print(f"\n🤖 Summarizing {len(articles)} international articles with AI...")
    
    for i, article in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] {article['title'][:60]}...")
        summary = summarize_article(article['text'])
        article['summary'] = summary
        if summary:
            print("  ✅ Summarized")
        else:
            print("  ⚠️ Summary failed")
    
    articles_by_region = {}
    for article in articles:
        region = article['region']
        if region not in articles_by_region:
            articles_by_region[region] = []
        articles_by_region[region].append(article)
    
    print(f"\n🎯 Generating quiz questions...")
    quiz_questions = generate_quiz(articles_by_region)
    if quiz_questions:
        print(f"  ✅ Generated {len(quiz_questions)} quiz questions")
    else:
        print(f"  ⚠️ Quiz generation failed")
    
    print(f"\n📧 Creating email...")
    html = create_html_email(articles_by_region, quiz_questions)
    
    print(f"📤 Sending email to {len(EMAIL_RECIPIENTS)} recipients...")
    send_email(html, len(articles))
    
    print(f"\n✅ Complete! Processed {len(articles)} international articles")
    print("=" * 60)

if __name__ == "__main__":
    main()
