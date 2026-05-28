import os
import requests
import feedparser
import html
import random
from datetime import datetime

FEED_URL = "https://phy-lab.com/feed"
TWITTER_HISTORY_FILE = "published_tweets.txt"

def normalize_url(url):
    if not url:
        return ""
    url = url.strip().lower()
    if url.endswith('/'):
        url = url[:-1]
    return url

def load_twitter_history():
    if os.path.exists(TWITTER_HISTORY_FILE):
        with open(TWITTER_HISTORY_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def get_archive_count_today(history_lines):
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    count = 0
    for line in history_lines:
        if "|| archive ||" in line and today_str in line:
            count += 1
    return count

def save_to_twitter_history(link, is_archive=False):
    normalized = normalize_url(link)
    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    type_str = "archive" if is_archive else "new"
    with open(TWITTER_HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{normalized} || {type_str} || {date_str}\n")

def send_tweet_mock(text):
    """طباعة التغريدة الجاهزة وإدارتها برمجياً بأمان"""
    print("🚀 نص التغريدة الجاهز والمعتمد للمنصة:")
    print("-" * 40)
    print(text)
    print("-" * 40)
    return True

def main():
    # استخدام متصفح وهمي لكسر جدار حماية خادم الووردبريس (Cloudflare/Wordfence)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(FEED_URL, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ فشل جلب الخلاصة من خادم الموقع. رمز الحالة: {response.status_code}")
            return
        
        # قراءة محتوى الـ XML مباشرة بعد الجلب الناجح
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"حدث خطأ أثناء الاتصال بخلاصة الموقع: {e}")
        return

    if not feed.entries:
        print("⚠️ لم يتمكن النظام من قراءة أي مقالات داخل خلاصة الموقع، تأكد من سلامة رابط الـ feed.")
        return

    history_lines = load_twitter_history()
    published_urls = set(normalize_url(line.split(" || ")[0]) for line in history_lines if line)
    
    latest_entry = feed.entries[0]
    normalized_latest_link = normalize_url(latest_entry.link)
    
    if normalized_latest_link not in published_urls:
        clean_title = html.unescape(latest_entry.title)
        tweet_text = (
            f"🎯 مقال علمي جديد في منصة معامل الفيزياء!\n\n"
            f"📝 【 {clean_title} 】\n\n"
            f"تفضلوا بالمعاينة والتجربة الرقمية عبر رابط المنصة المباشر:\n"
            f"{latest_entry.link}\n\n"
            f"تابعونا للمزيد 🔭: @Phylab5\n"
            f"#معامل_الفيزياء #محاكاة_علمية"
        )
        if send_tweet_mock(tweet_text):
            save_to_twitter_history(latest_entry.link, is_archive=False)
            print("🎯 تم معالجة وحفظ المقال الجديد في الذاكرة بنجاح!")
        return

    archive_sent_today = get_archive_count_today(history_lines)
    print(f"تغريدات الأرشيف المرسلة اليوم: {archive_sent_today}/2")
    
    if archive_sent_today < 2:
        unpublications = [entry for entry in feed.entries if normalize_url(entry.link) not in published_urls]
        if unpublications:
            archive_entry = random.choice(unpublications)
            clean_title = html.unescape(archive_entry.title)
            tweet_text = (
                f"📚 من أرشيف معامل الفيزياء المتميزة\n\n"
                f"📝 【 {clean_title} 】\n\n"
                f"اكتشف المختبرات الافتراضية والأدوات البرمجية المتوفرة:\n"
                f"{archive_entry.link}\n\n"
                f"للمتابعة عبر تويتر 💻: @Phylab5\n"
                f"#معامل_الفيزياء #Phy_Lab"
            )
            if send_tweet_mock(tweet_text):
                save_to_twitter_history(archive_entry.link, is_archive=True)
                print("📚 تم معالجة وتخزين تغريدة الأرشيف في الذاكرة بنجاح!")
        else:
            print("كل مقالات الموقع المتاحة في الخلاصة تم معالجتها وتغريدها مسبقاً.")
    else:
        print("تم الوصول للحد الأقصى لتغريدات الأرشيف اليوم.")

if __name__ == "__main__":
    main()
