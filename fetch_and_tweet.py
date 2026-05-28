import os
import requests
import feedparser
import html
import random
from datetime import datetime
from requests_oauthlib import OAuth1

# استدعاء مفاتيح تويتر الأربعة الأصلية التي استخرجناها من لوحة المطورين في البداية
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

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

def send_tweet_direct(text):
    """إرسال التغريدة مباشرة عبر واجهة برمجية تتخطى قيود الأرصدة التلقائية"""
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
    
    # نرسل البيانات كـ JSON مع تحديد الـ Content-Type ليتوافق مع الحساب المجاني
    headers = {"Content-Type": "application/json"}
    payload = {"text": text}
    
    try:
        response = requests.post(url, auth=auth, json=payload, headers=headers)
        if response.status_code == 201:
            return True
        else:
            print(f"❌ فشل النشر المباشر. رمز الحالة: {response.status_code}")
            print(f"📋 رد السيرفر: {response.text}")
            return False
    except Exception as e:
        print(f"حدث خطأ أثناء الاتصال المباشر بإكس: {e}")
        return False

def main():
    if not API_KEY or not API_SECRET or not ACCESS_TOKEN or not ACCESS_SECRET:
        print("❌ خطأ: مفاتيح تويتر الأربعة الأصلية غير متوفرة في إعدادات جيتهاب Secrets.")
        return

    feed = feedparser.parse(FEED_URL)
    if not feed.entries:
        print("خلاصة الموقع فارغة حالياً.")
        return

    history_lines = load_twitter_history()
    published_urls = set(normalize_url(line.split(" || ")[0]) for line in history_lines if line)
    
    # 1. مسار المقالات الجديدة
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
        print(f"جاري إرسال مقال جديد مباشرة لـ تويتر: {clean_title}")
        if send_tweet_direct(tweet_text):
            save_to_twitter_history(latest_entry.link, is_archive=False)
            print("🎯 تم التغريد بنجاح وحفظ الرابط للجديد!")
        return

    # 2. مسار الأرشيف
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
            print(f"جاري إرسال مقال أرشيفي مباشرة لـ تويتر: {clean_title}")
            if send_tweet_direct(tweet_text):
                save_to_twitter_history(archive_entry.link, is_archive=True)
                print("📚 تم تغريد الأرشيف بنجاح!")
        else:
            print("كل المقالات المتاحة تم تغريدها مسبقاً.")
    else:
        print("تم الوصول للحد الأقصى لتغريدات الأرشيف اليوم.")

if __name__ == "__main__":
    main()
