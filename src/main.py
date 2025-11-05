# --- شروع اسکریپت Trend-Analyzer (نسخه نهایی با Endpoint صحیح) ---

import os
import asyncio
import re 
from pytrends.request import TrendReq
import google.generativeai as genai
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID 

# --- تابع اصلی ---
async def main(context):
    context.log("فانکشن Trend-Analyzer (نسخه نهایی) شروع به کار کرد...")

    try:
        # ۱. دریافت کلیدهای مخفی
        GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
        APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")
        APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
        APPWRITE_DATABASE_ID = os.environ.get("APPWRITE_DATABASE_ID") 
        APPWRITE_COLLECTION_ID = os.environ.get("APPWRITE_COLLECTION_ID") 
        
        # --- اصلاحیه کلیدی ---
        # خواندن اندپوینت (Endpoint) منطقه‌ای از متغیرهای داخلی Appwrite
        # این متغیر به صورت خودکار توسط Appwrite تزریق می‌شود
        APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
        
        # بررسی کلیدهای ضروری (اندپوینت هم اضافه شد)
        if not (GOOGLE_AI_API_KEY and APPWRITE_API_KEY and APPWRITE_PROJECT_ID and APPWRITE_DATABASE_ID and APPWRITE_COLLECTION_ID and APPWRITE_ENDPOINT):
            context.log("خطای حیاتی: یک یا چند متغیر محیطی (API Keys, IDها یا Endpoint) تنظیم نشده‌اند.")
            return context.res.json({"success": False, "error": "Missing environment variables"})

        # ۲. تنظیم کلاینت Appwrite
        client = Client()
        
        # --- رفع باگ ---
        # ما از اندپوینت منطقه‌ای (که از متغیرها خواندیم) استفاده می‌کنیم، نه آدرس عمومی
        client.set_endpoint(APPWRITE_ENDPOINT)
        # --- پایان رفع باگ ---
        
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

        url_match = re.search(r'(https?://(www\.)?(youtube\.com|youtu\.be)/[^\s]+)', full_response_text)
        if url_match:
            video_url = url_match.group(0)
            reportage_text = full_response_text.replace(video_url, "").strip()
            context.log(f"لینک ویدیو با موفقیت استخراج شد: {video_url}")
        else:
            context.log("هیچ لینک ویدیویی در پاسخ Gemini یافت نشد.")

        # ۸. ذخیره‌سازی داده‌ها در دیتابیس Appwrite
        new_document_data = {
            'title': top_topic,
            'status': 'ready_to_publish',
            'source_url': f"https://trends.google.com/trends/explore?q={top_topic.replace(' ', '%20')}",
            'raw_content': prompt, 
            'reportage_text': reportage_text,
            'featured_media_url': video_url,
            'hashtags': ['اخبار_بازی', 'گیم_موبایل', top_topic.replace(' ', '_')] 
        }
        
        # ما منتظر می‌مانیم (await) تا ایجاد داکیومنت کامل شود
        doc = await db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID,
            document_id=ID.unique(), 
            data=new_document_data
        )
        context.log(f"رپورتاژ جدید با موفقیت در دیتابیس Articles ذخیره شد. Document ID: {doc['$id']}")

        return context.res.json({"success": True, "document_id": doc['$id']})

    except Exception as e:
        context.error(f"خطای بحرانی در Trend-Analyzer رخ داد: {str(e)}")
        return context.res.json({"success": False, "error": str(e)})
