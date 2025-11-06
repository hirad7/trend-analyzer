import os
import asyncio
import requests
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.services.storage import Storage
from appwrite.query import Query
import uuid  # برای ساخت row_id منحصر به فرد

async def main(context):
    context.log("فانکشن تحلیل ترند (با Grok + Flux.1) شروع شد...")

    try:
        # === ۱. دریافت متغیرها ===
        XAI_API_KEY = os.environ.get("XAI_API_KEY")
        APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")
        APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
        APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
        APPWRITE_DATABASE_ID = os.environ.get("APPWRITE_DATABASE_ID")
        APPWRITE_COLLECTION_ID = os.environ.get("APPWRITE_COLLECTION_ID")
        APPWRITE_BUCKET_ID = os.environ.get("APPWRITE_BUCKET_ID", "images")

        if not XAI_API_KEY:
            raise Exception("XAI_API_KEY پیدا نشد!")

        # === ۲. تنظیم کلاینت Appwrite ===
        client = Client()
        client.set_endpoint(APPWRITE_ENDPOINT)
        client.set_project(APPWRITE_PROJECT_ID)
        client.set_key(APPWRITE_API_KEY)
        db = TablesDB(client)
        storage = Storage(client)
        context.log("کلاینت Appwrite آماده شد.")

        # === ۳. تولید ترند (مثال) ===
        trend_topic = "به‌روزرسانی جدید Genshin Impact"
        context.log(f"ترند پیدا شد: {trend_topic}")

        # === ۴. تولید متن (reportage) با Grok-4 ===
        grok_chat_url = "https://api.x.ai/v1/chat/completions"
        reportage_prompt = f"یک رپورتاژ جذاب، کوتاه و حرفه‌ای فارسی در مورد '{trend_topic}' بنویس. فقط متن، بدون مقدمه."

        chat_response = requests.post(
            grok_chat_url,
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-4-latest",
                "messages": [{"role": "user", "content": reportage_prompt}],
                "temperature": 0.7,
                "max_tokens": 500
            }
        )

        if chat_response.status_code == 200:
            reportage_text = chat_response.json()["choices"][0]["message"]["content"].strip()
        else:
            context.log(f"خطای Grok Chat: {chat_response.text}")
            reportage_text = f"محتوای پیش‌فرض: {trend_topic}"
        context.log("رپورتاژ ساخته شد.")

        # === ۵. تولید عکس با Grok (Flux.1) ===
        image_prompt = f"پوستر حرفه‌ای گیمینگ موبایل از '{trend_topic}'، شخصیت اصلی در مرکز، افکت‌های نئونی، رنگ‌های زنده، کیفیت 4K، سبک بازی‌های AAA، بدون متن"

        image_response = requests.post(
            "https://api.x.ai/v1/images/generations",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "flux.1",
                "prompt": image_prompt,
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 30
            }
        )

        final_image_url = None
        if image_response.status_code == 200:
            image_url = image_response.json()["data"][0]["url"]
            context.log(f"عکس ساخته شد: {image_url}")

            # دانلود و آپلود به Appwrite Storage
            img_data = requests.get(image_url).content
            uploaded = storage.create_file(
                bucket_id=APPWRITE_BUCKET_ID,
                file_id='unique()',
                file=img_data,
                filename=f"{trend_topic.replace(' ', '_')}.png"
            )
            final_image_url = f"https://cloud.appwrite.io/v1/storage/buckets/{APPWRITE_BUCKET_ID}/files/{uploaded['$id']}/view?project={APPWRITE_PROJECT_ID}"
        else:
            context.log(f"خطای Grok Image: {image_response.text}")

        # === ۶. ذخیره در دیتابیس با row_id منحصر به فرد ===
        row_id = str(uuid.uuid4())  # ساخت ID منحصر به فرد

        data = {
            'title': trend_topic,
            'reportage_text': reportage_text,
            'image_url': final_image_url or 'بدون عکس',
            'status': 'ready_to_publish',
            'source_url': 'https://example.com',
            'featured_media_url': 'https://example.com/video',
            'hashtags': ['گیمینگ', 'بازی_موبایل', 'ترند', 'GenshinImpact']
        }

        db.create_row(
            database_id=APPWRITE_DATABASE_ID,
            table_id=APPWRITE_COLLECTION_ID,
            row_id=row_id,  # اینجا اضافه شد!
            data=data
        )
        context.log(f"مقاله با row_id: {row_id} ذخیره شد.")

        return context.res.json({
            "success": True,
            "message": "مقاله آماده انتشار شد!",
            "row_id": row_id
        })

    except Exception as e:
        context.error(f"خطای بحرانی: {str(e)}")
        return context.res.json({"success": False, "error": str(e)})
