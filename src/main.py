import os
import asyncio
import requests
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.services.storage import Storage
from appwrite.query import Query
import base64

async def main(context):
    context.log("فانکشن تحلیل ترند (خوداصلاح‌شونده با لیست مدل‌ها) شروع شد...")

    try:
        # ۱. دریافت متغیرها
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")
        APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
        APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
        APPWRITE_DATABASE_ID = os.environ.get("APPWRITE_DATABASE_ID")
        APPWRITE_COLLECTION_ID = os.environ.get("APPWRITE_COLLECTION_ID")
        APPWRITE_BUCKET_ID = os.environ.get("APPWRITE_BUCKET_ID", "images")

        # ۲. تنظیم کلاینت Appwrite
        client = Client()
        client.set_endpoint(APPWRITE_ENDPOINT)
        client.set_project(APPWRITE_PROJECT_ID)
        client.set_key(APPWRITE_API_KEY)
        db = TablesDB(client)
        storage = Storage(client)
        context.log("کلاینت Appwrite آماده شد.")

        # ۳. خوداصلاح: لیست مدل‌های مجاز رو از API بگیر
        list_models_url = f"https://generativelanguage.googleapis.com/v1/models?key={GOOGLE_API_KEY}"
        list_response = requests.get(list_models_url)
        list_json = list_response.json()
        
        if 'error' in list_json:
            raise Exception(f"خطای لیست مدل‌ها: {list_json['error']['message']}")
        
        available_models = [model['name'] for model in list_json.get('models', []) if 'generateContent' in model.get('supportedGenerationMethods', [])]
        context.log(f"مدل‌های مجاز پیدا شد: {', '.join(available_models)}")
        
        if not available_models:
            raise Exception("هیچ مدلی مجاز پیدا نشد – API key رو چک کن.")
        
        # انتخاب مدل مناسب (اولین که flash یا pro داره، اولویت به image support)
        selected_model = next((m for m in available_models if 'flash' in m or 'pro' in m), available_models[0])
        context.log(f"مدل انتخاب‌شده: {selected_model}")

        # ۴. چک ترندها (مثال)
        trend_topic = "به‌روزرسانی جدید در بازی‌های موبایل"
        context.log(f"ترند پیدا شد: {trend_topic}")

        # ۵. ساخت reportage با مدل انتخاب‌شده
        gemini_prompt = f"یک رپورتاژ خلاقانه و جذاب فارسی در مورد '{trend_topic}' بنویس، کوتاه و engaging برای شبکه‌های اجتماعی."
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={GOOGLE_API_KEY}"
        gemini_body = {"contents": [{"parts": [{"text": gemini_prompt}]}]}
        response = requests.post(gemini_url, json=gemini_body)
        response_json = response.json()
        
        if 'error' in response_json:
            raise Exception(f"خطای API: {response_json['error']['message']}")
        elif 'candidates' not in response_json or not response_json['candidates']:
            context.log("هیچ پاسخی نیامد.")
            reportage_text = "محتوای پیش‌فرض: " + trend_topic
        else:
            reportage_text = response_json['candidates'][0]['content']['parts'][0]['text']
        context.log("رپورتاژ ساخته شد.")

        # ۶. ساخت عکس با مدل انتخاب‌شده (اگر support کنه)
        image_prompt = f"یک عکس جذاب و هیجانی از '{trend_topic}' در سبک گیمینگ موبایل، با رنگ‌های زنده، المان‌های بازی مثل شخصیت‌ها و افکت‌ها، و عنوان '{trend_topic}' در وسط. فرمت PNG."
        image_body = {
            "contents": [{"parts": [{"text": image_prompt}]}],
            "generationConfig": {"response_mime_type": "image/png"}
        }
        image_response = requests.post(gemini_url, json=image_body)
        image_json = image_response.json()
        
        image_url = None
        if 'error' in image_json:
            context.log(f"خطای ساخت عکس: {image_json['error']['message']}")
        elif 'candidates' not in image_json or not image_json['candidates']:
            context.log("هیچ عکسی ساخته نشد.")
        else:
            image_base64 = image_json['candidates'][0]['content']['parts'][0].get('inline_data', {}).get('data', None)
            if image_base64:
                image_data = base64.b64decode(image_base64)
                file_name = f"{trend_topic.replace(' ', '_')}.png"
                uploaded_file = storage.create_file(
                    bucket_id=APPWRITE_BUCKET_ID,
                    file_id='unique()',
                    file=image_data,
                    filename=file_name
                )
                image_url = f"https://cloud.appwrite.io/v1/storage/buckets/{APPWRITE_BUCKET_ID}/files/{uploaded_file['$id']}/view?project={APPWRITE_PROJECT_ID}"
        context.log("عکس AI پردازش شد.")

        # ۷. ذخیره در DB
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
