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

def send_tweet_via_webhook(text):
    """
    بما أن الـ API مغلق، الكود سيقوم بطباعة نص التغريدة الجاهز في السجلات 
    تمهيداً لدفعها عبر نظام النشر الآلي المستقر.
    """
    print("🚀 نص التغريدة الجاهز للنشر:")
    print("-" * 40)
    print(text)
    print("-" * 40)
    # لإتمام الربط التلقائي بدون قيود، يفضل استخدام بروتوكول التليجرام الذي يعمل معك بنجاح 100%
    return True

def main():
    feed = feedparser.parse(FEED_URL)
    if not feed.entries:
        print("خلاصة الموقع فارغة حالياً.")
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
        if send_tweet_via_webhook(tweet_text):
            save_to_twitter_history(latest_entry.link, is_archive=False)
            print("🎯 تم معالجة التغريدة الجديدة بنجاح!")
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
            if send_tweet_via_webhook(tweet_text):
                save_to_twitter_history(archive_entry.link, is_archive=True)
                print("📚 تم معالجة تغريدة الأرشيف بنجاح!")
        else:
            print("كل المقالات المتاحة تم معالجتها مسبقاً.")
    else:
        print("تم الوصول للحد الأقصى اليوم.")

if __name__ == "__main__":
    main()
