# --- شروع اسکریپت Trend-Analyzer (نسخه نهایی با ذخیره‌سازی در دیتابیس) ---

import os
import asyncio
import re # کتابخانه لازم برای پیدا کردن لینک ویدیو
from pytrends.request import TrendReq
import google.generativeai as genai
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID # برای ساختن ID یونیک برای هر مقاله

# --- تابع اصلی ---
async def main(context):
    context.log("فانکشن Trend-Analyzer (نسخه نهایی) شروع به کار کرد...")

    try:
        # ۱. دریافت کلیدهای مخفی
        GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
        APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")
        APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
        APPWRITE_DATABASE_ID = os.environ.get("APPWRITE_DATABASE_ID") # آیدی دیتابیس NewsDB
        APPWRITE_COLLECTION_ID = os.environ.get("APPWRITE_COLLECTION_ID") # آیدی جدول Articles
        
        # بررسی کلیدهای ضروری
        if not (GOOGLE_AI_API_KEY and APPWRITE_API_KEY and APPWRITE_PROJECT_ID and APPWRITE_DATABASE_ID and APPWRITE_COLLECTION_ID):
            context.log("خطای حیاتی: یک یا چند متغیر محیطی (API Keys یا IDها) تنظیم نشده‌اند.")
            context.log("متغیرهای لازم: GOOGLE_AI_API_KEY, APPWRITE_API_KEY, APPWRITE_PROJECT_ID, APPWRITE_DATABASE_ID, APPWRITE_COLLECTION_ID")
            return context.res.json({"success": False, "error": "Missing environment variables"})

        # ۲. تنظیم کلاینت Appwrite
        client = Client()
        client.set_endpoint("https://cloud.appwrite.io/v1")
        client.set_project(APPWRITE_PROJECT_ID)
        client.set_key(APPWRITE_API_KEY)
        db = Databases(client)
        context.log("کلاینت Appwrite با موفقیت پیکربندی شد.")

        # ۳. تنظیم هوش مصنوعی Gemini
        genai.configure(api_key=GOOGLE_AI_API_KEY)
        model = genai.GenerativeModel('models/gemini-pro-latest')
        context.log("هوش مصنوعی Gemini با موفقیت پیکربندی شد.")

        # ۴. اتصال به گوگل ترندز
        pytrends = TrendReq(hl='en-US', tz=360)
        keywords = ["mobile game", "genshin impact", "call of duty mobile", "pubg mobile"]
        pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='', gprop='')
        related_data = pytrends.related_topics()
        context.log("داده‌های گوگل ترندز دریافت شد.")

        # ۵. استخراج داغ‌ترین موضوع
        top_topic = "New update in mobile gaming" # موضوع نمونه
        if keywords[0] in related_data and not related_data[keywords[0]]['rising'].empty:
            top_rising = related_data[keywords[0]]['rising']
            top_topic = top_rising.iloc[0]['topic_title']
        context.log(f"موضوع داغ شناسایی شده: {top_topic}")

        # ۶. ارسال موضوع به Gemini برای تحلیل و رپورتاژ
        prompt = (
            f"موضوع '{top_topic}' در حال حاضر در گوگل ترندز داغ است."
            "لطفاً به عنوان یک منتقد برتر بازی‌های موبایل، در اینترنت جستجو کن و یک «رپورتاژ» خلاقانه و دقیق به زبان فارسی بنویس."
            "این رپورتاژ باید شامل تحلیل، دلیل داغ شدن، و نقد کوتاه باشد."
            "همچنین، لطفاً بهترین لینک ویدیوی YouTube (تریلر یا گیم‌پلی) مرتبط با این موضوع را پیدا کن و فقط لینک خام آن را در انتهای پاسخ خود در یک خط جداگانه قرار بده."
        )
        
        response = await model.generate_content_async(prompt)
        context.log("پاسخ از Gemini دریافت شد.")
        
        # ۷. پردازش و جداسازی پاسخ Gemini
        full_response_text = response.text
        reportage_text = full_response_text
        video_url = None

        # تلاش برای پیدا کردن لینک یوتیوب در متن
        url_match = re.search(r'(https?://(www\.)?(youtube\.com|youtu\.be)/[^\s]+)', full_response_text)
        if url_match:
            video_url = url_match.group(0)
            # حذف لینک از متن اصلی رپورتاژ
            reportage_text = full_response_text.replace(video_
