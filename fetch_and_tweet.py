import os
import time
import requests
import feedparser
import html
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

FEED_URL = "https://phy-lab.com/feed"
TWITTER_HISTORY_FILE = "published_tweets.txt"
X_USER = os.getenv("X_USERNAME")
X_PASS = os.getenv("X_PASSWORD")

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

def send_tweet_via_browser(text):
    """فتح متصفح وهمي صامت وتسجيل الدخول إلى إكس ونشر التغريدة فعلياً"""
    if not X_USER or not X_PASS:
        print("❌ خطأ: حساب تويتر أو كلمة المرور غير متوفرة في جيتهاب Secrets.")
        return False

    with sync_playwright() as p:
        try:
            print("🌐 جاري تشغيل المتصفح الوهمي الصامت...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            
            print("🔐 جاري الدخول إلى صفحة تسجيل دخول إكس...")
            page.goto("https://x.com/i/flow/login", timeout=60000)
            
            # انتظر واكتب اسم المستخدم
            page.wait_for_selector("input[autocomplete='username']", timeout=20000)
            page.fill("input[autocomplete='username']", X_USER)
            page.click("text=Next")
            
            # انتظر واكتب كلمة المرور
            page.wait_for_selector("input[name='password']", timeout=20000)
            page.fill("input[name='password']", X_PASS)
            page.click("data-testid=LoginForm_Login_Button")
            
            print("🚀 تم تسجيل الدخول بأمان، جاري فتح صندوق التغريد الحقيقي...")
            page.wait_for_selector("data-testid=SideNav_NewTweet_Button", timeout=30000)
            
            # فتح صندوق التغريد والكتابة فيه
            page.click("data-testid=SideNav_NewTweet_Button")
            page.wait_for_selector("data-testid=tweetTextarea_0", timeout=20000)
            page.fill("data-testid=tweetTextarea_0", text)
            
            # الضغط على زر نشر (Tweet)
            print("✍️ جاري إرسال التغريدة العلمية إلى الحساب الآن...")
            page.click("data-testid=tweetButton")
            
            # انتظار 5 ثوانٍ للتأكد من معالجة السيرفر للتغريدة قبل الإغلاق
            time.sleep(5)
            print("🎯 [نجاح فعلي] تم نشر التغريدة بنجاح على الحساب!")
            browser.close()
            return True
            
        except Exception as e:
            print(f"❌ حدث خطأ أثناء عملية الأتمتة بالمتصفح: {e}")
            return False

def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(FEED_URL, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ فشل جلب الخلاصة من خادم الموقع. رمز الحالة: {response.status_code}")
            return
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"حدث خطأ أثناء الاتصال بخلاصة الموقع: {e}")
        return

    if not feed.entries:
        print("⚠️ لم يتمكن النظام من قراءة خلاصة الموقع.")
        return

    history_lines = load_twitter_history()
    published_urls = set(normalize_url(line.split(" || ")[0]) for line in history_lines if line)
    
    latest_entry = feed.entries[0]
    normalized_latest_link = normalize_url(latest_entry.link)
    
    # تأكيد طباعة النص قبل النشر للمعاينة
    clean_title = html.unescape(latest_entry.title)
    tweet_text = (
        f"🎯 مقال علمي جديد في منصة معامل الفيزياء!\n\n"
        f"📝 【 {clean_title} 】\n\n"
        f"تفضلوا بالمعاينة والتجربة الرقمية عبر رابط المنصة المباشر:\n"
        f"{latest_entry.link}\n\n"
        f"تابعونا للمزيد 🔭: @Phylab5\n"
        f"#معامل_الفيزياء #محاكاة_علمية"
    )
    
    if normalized_latest_link not in published_urls:
        print(f"🔄 مقال جديد مكتشف، جاري إطلاق المتصفح للنشر: {clean_title}")
        if send_tweet_via_browser(tweet_text):
            save_to_twitter_history(latest_entry.link, is_archive=False)
        return

    archive_sent_today = get_archive_count_today(history_lines)
    print(f"تغريدات الأرشيف المرسلة اليوم: {archive_sent_today}/2")
    
    if archive_sent_today < 2:
        unpublications = [entry for entry in feed.entries if normalize_url(entry.link) not in published_urls]
        if unpublications:
            archive_entry = random.choice(unpublications)
            clean_title = html.unescape(archive_entry.title)
            archive_text = (
                f"📚 من أرشيف معامل الفيزياء المتميزة\n\n"
                f"📝 【 {clean_title} 】\n\n"
                f"اكتشف المختبرات الافتراضية والأدوات البرمجية المتوفرة:\n"
                f"{archive_entry.link}\n\n"
                f"للمتابعة عبر تويتر 💻: @Phylab5\n"
                f"#معامل_الفيزياء #Phy_Lab"
            )
            print(f"🔄 جاري إطلاق المتصفح لنشر مقال أرشيفي: {clean_title}")
            if send_tweet_via_browser(archive_text):
                save_to_twitter_history(archive_entry.link, is_archive=True)
        else:
            print("كل المقالات متاحة تم نشرها مسبقاً.")
    else:
        print("تم الوصول للحد الأقصى لتغريدات الأرشيف اليوم.")

if __name__ == "__main__":
    main()
