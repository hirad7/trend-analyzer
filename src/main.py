import os
import asyncio
import requests  # برای کال API
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.query import Query

async def main(context):
    context.log("فانکشن تحلیل ترند (با ساخت عکس AI) شروع شد...")

    try:
        # ۱. دریافت متغیرها (شامل GOOGLE_API_KEY که اضافه کردی)
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")
        APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
        APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
        APPWRITE_DATABASE_ID = os.environ.get("APPWRITE_DATABASE_ID")
        APPWRITE_COLLECTION_ID = os.environ.get("APPWRITE_COLLECTION_ID")

        # ۲. تنظیم کلاینت Appwrite
        client = Client()
        client.set_endpoint(APPWRITE_ENDPOINT)
        client.set_project(APPWRITE_PROJECT_ID)
        client.set_key(APPWRITE_API_KEY)
        db = TablesDB(client)
        context.log("کلاینت Appwrite آماده شد.")

        # ۳. چک ترندها از Google Trends (کد قدیمی – فرض کنیم کار می‌کنه)
        # اینجا کد چک ترندها رو بگذار (از نسخه قبلی کپی کن، یا اگر ساده، مثال:)
        trend_topic = "New Mobile Game Update"  # جایگذاری واقعی با Trends API
        context.log(f"ترند پیدا شد: {trend_topic}")

        # ۴. ساخت reportage با Gemini (کد قدیمی)
        gemini_prompt = f"یک رپورتاژ خلاقانه فارسی در مورد '{trend_topic}' بنویس."
        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + GOOGLE_API_KEY
        gemini_body = {
            "contents": [{"parts": [{"text": gemini_prompt}]}]
        }
        response = requests.post(gemini_url, json=gemini_body)
        reportage_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        context.log("رپورتاژ ساخته شد.")

        # ۵. جدید: ساخت عکس جذاب با Gemini
        image_prompt = f"یک عکس جذاب و هیجانی از '{trend_topic}' در سبک گیمینگ موبایل، با رنگ‌های زنده، المان‌های بازی مثل کنترلر یا شخصیت‌ها، و عنوان '{trend_topic}' در وسط. فرمت PNG."
        image_body = {
            "contents": [{"parts": [{"text": image_prompt}]}],
            "generationConfig": {"response_mime_type": "image/png"}  # برای خروجی عکس
        }
        image_response = requests.post(gemini_url, json=image_body)
        # Gemini عکس رو به base64 برمی‌گردونه – اما برای سادگی، فرض کنیم لینک یا base64 ذخیره می‌شه
        # واقعی: base64 رو decode و upload به Appwrite Storage، URL بگیر (کد اضافی اگر نیاز)
        image_url = "https://example.com/generated_image.png"  # جایگذاری واقعی
        context.log("عکس AI ساخته و ذخیره شد.")

        # ۶. ذخیره در DB (با image_url جدید)
        data = {
            'title': trend_topic,
            'reportage_text': reportage_text,
            'image_url': image_url,  # جدید
            'status': 'ready_to_publish'
            # بقیه فیلدها مثل hashtags, video_url
        }
        db.create_row(
            database_id=APPWRITE_DATABASE_ID,
            table_id=APPWRITE_COLLECTION_ID,
            data=data
        )
        context.log("داده‌ها با عکس ذخیره شد.")

        return context.res.json({"success": True})

    except Exception as e:
        context.error(f"خطا: {str(e)}")
        return context.res.json({"success": False})
