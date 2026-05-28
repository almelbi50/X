import os
import requests
import feedparser
import re
import html
import random
from datetime import datetime

# استدعاء المفاتيح الأمنية من جيتهاب
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")
PROFILE_ID = os.getenv("BUFFER_PROFILE_ID")

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

def send_tweet_via_buffer(text):
    """إرسال التغريدة وتمرير التوكن بالتوافق مع الـ OIDC Tokens لـ Buffer"""
    # نمرر التوكن مباشرة في رابط الطلب لتخطي حظر الـ OIDC في الـ Headers
    url = f"https://api.bufferapp.com/1/updates/create.json?access_token={BUFFER_TOKEN}"
    
    payload = {
        "profile_ids[]": [PROFILE_ID],
        "text": text,
        "shorten": False,
        "now": True  # النشر الفوري والمباشر
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ فشل النشر عبر Buffer. رمز الحالة: {response.status_code}")
            print(f"📋 رد السيرفر: {response.text}")
            return False
    except Exception as e:
        print(f"حدث خطأ أثناء الاتصال بـ Buffer: {e}")
        return False

def main():
    if not BUFFER_TOKEN or not PROFILE_ID:
        print("❌ خطأ: مفاتيح Buffer_Access_Token أو Profile_ID غير متوفرة في جيتهاب.")
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
        print(f"جاري إرسال مقال جديد لـ تويتر عبر Buffer: {clean_title}")
        if send_tweet_via_buffer(tweet_text):
            save_to_twitter_history(latest_entry.link, is_archive=False)
            print("🎯 تم التغريد وحفظ الرابط للجديد بنجاح!")
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
            print(f"جاري إرسال مقال أرشيفي لـ تويتر عبر Buffer: {clean_title}")
            if send_tweet_via_buffer(tweet_text):
                save_to_twitter_history(archive_entry.link, is_archive=True)
                print("📚 تم تغريد الأرشيف بنجاح!")
        else:
            print("كل المقالات المتاحة تم تغريدها مسبقاً.")
    else:
        print("تم الوصول للحد الأقصى لتغريدات الأرشيف اليوم.")

if __name__ == "__main__":
    main()
