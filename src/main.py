import os
import asyncio
import requests  # برای کال API
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.query import Query

async def main(context):
    context.log("فانکشن تحلیل ترند (با مدل fix و عکس AI) شروع شد...")

    try:
        # ۱. دریافت متغیرها
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

        # ۳. چک ترندها (مثال – کد واقعی Trends رو اضافه کن اگر داری)
        trend_topic = "به‌روزرسانی جدید در بازی‌های موبایل"  # جایگذاری با ترند واقعی
        context.log(f"ترند پیدا شد: {trend_topic}")

        # ۴. ساخت reportage با Gemini (مدل fix: gemini-1.5-flash)
        gemini_prompt = f"یک رپورتاژ خلاقانه و جذاب فارسی در مورد '{trend_topic}' بنویس، کوتاه و engaging برای شبکه‌های اجتماعی."
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
        gemini_body = {
            "contents": [{"parts": [{"text": gemini_prompt}]}]
        }
        response = requests.post(gemini_url, json=gemini_body)
        response_json = response.json()
        
        if 'error' in response_json:
            raise Exception(f"خطای API: {response_json['error']['message']}")
        elif 'candidates' not in response_json or not response_json['candidates']:
            context.log("هیچ پاسخی از Gemini نیامد: " + str(response_json.get('promptFeedback', 'نامشخص')))
            reportage_text = "محتوای پیش‌فرض: " + trend_topic
        else:
            reportage_text = response_json['candidates'][0]['content']['parts'][0]['text']
        context.log("رپورتاژ ساخته شد.")

        # ۵. ساخت عکس با Gemini (مدل fix، با fallback اگر support نشد)
        image_prompt = f"یک عکس جذاب و هیجانی از '{trend_topic}' در سبک گیمینگ موبایل، با رنگ‌های زنده، المان‌های بازی مثل شخصیت‌ها و افکت‌ها، و عنوان '{trend_topic}' در وسط. فرمت PNG."
        image_body = {
            "contents": [{"parts": [{"text": image_prompt}]}],
            "generationConfig": {"response_mime_type": "image/png"}
        }
        image_response = requests.post(gemini_url, json=image_body)
        image_json = image_response.json()
        
        if 'error' in image_json:
            context.log(f"خطای ساخت عکس: {image_json['error']['message']}")
            image_url = None
        elif 'candidates' not in image_json or not image_json['candidates']:
            context.log("هیچ عکسی ساخته نشد: " + str(image_json.get('promptFeedback', 'نامشخص')))
            image_url = None
        else:
            # base64 image رو بگیر و upload به Appwrite Storage (برای تست، placeholder – بعداً real upload اضافه می‌کنیم)
            image_base64 = image_json['candidates'][0]['content']['parts'][0].get('inline_data', {}).get('data', None)
            image_url = "https://example.com/generated_image.png" if image_base64 else None  # واقعی: upload کن
        context.log("عکس AI پردازش شد.")

        # ۶. ذخیره در DB
        data = {
            'title': trend_topic,
            'reportage_text': reportage_text,
            'image_url': image_url if image_url else 'بدون عکس',
            'status': 'ready_to_publish'
        }
        db.create_row(
            database_id=APPWRITE_DATABASE_ID,
            table_id=APPWRITE_COLLECTION_ID,
            data=data
        )
        context.log("داده‌ها ذخیره شد.")

        return context.res.json({"success": True})

    except Exception as e:
        context.error(f"خطا: {str(e)}")
        return context.res.json({"success": False})
