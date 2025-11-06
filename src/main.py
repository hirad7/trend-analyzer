import os
import asyncio
import requests
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.services.storage import Storage
from appwrite.query import Query
from appwrite.input_file import InputFile  # جدید
import uuid

async def main(context):
    context.log("فانکشن تحلیل ترند (با عکس از وب – نهایی) شروع شد...")

    try:
        # === ۱. دریافت متغیرها ===
        APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")
        APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
        APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
        APPWRITE_DATABASE_ID = os.environ.get("APPWRITE_DATABASE_ID")
        APPWRITE_COLLECTION_ID = os.environ.get("APPWRITE_COLLECTION_ID")
        APPWRITE_BUCKET_ID = os.environ.get("APPWRITE_BUCKET_ID", "images")

        # === ۲. تنظیم کلاینت Appwrite ===
        client = Client()
        client.set_endpoint(APPWRITE_ENDPOINT)
        client.set_project(APPWRITE_PROJECT_ID)
        client.set_key(APPWRITE_API_KEY)
        db = TablesDB(client)
        storage = Storage(client)
        context.log("کلاینت Appwrite آماده شد.")

        # === ۳. تولید ترند ===
        trend_topic = "به‌روزرسانی جدید Genshin Impact"
        context.log(f"ترند پیدا شد: {trend_topic}")

        # === ۴. متن engaging پیش‌فرض ===
        reportage_text = f"{trend_topic}: بازی Genshin Impact با ویژگی‌های جدید مثل quests حماسی، گرافیک بهتر و ایونت‌های ویژه، گیمرها رو به هیجان می‌آره! آیا آماده‌ای برای ماجراجویی؟ #GenshinImpact"
        context.log("متن engaging ساخته شد.")

        # === ۵. دانلود عکس مرتبط از وب (کم‌حجم) ===
        possible_images = [
            "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=512&h=512&fit=crop",
            "https://wallpaperaccess.com/full/1668x2224.jpg?w=512&h=512&fit=crop"
        ]

        img_data = None
        final_image_url = None
        for img_url in possible_images:
            try:
                img_response = requests.get(img_url, timeout=5)
                if img_response.status_code == 200 and len(img_response.content) < 200000:
                    img_data = img_response.content
                    context.log(f"عکس از وب دانلود شد (حجم: {len(img_data)} bytes)")
                    break
            except Exception as e:
                context.log(f"خطای دانلود {img_url}: {str(e)}")
                continue

        if img_data:
            # آپلود با InputFile (متادیتا اضافه شد)
            uploaded = storage.create_file(
                bucket_id=APPWRITE_BUCKET_ID,
                file_id='unique()',
                file=InputFile.from_bytes(img_data, "image.png")  # متادیتا + نام
            )
            final_image_url = f"https://cloud.appwrite.io/v1/storage/buckets/{APPWRITE_BUCKET_ID}/files/{uploaded['$id']}/view?project={APPWRITE_PROJECT_ID}"
            context.log(f"عکس کم‌حجم آپلود شد: {final_image_url}")
        else:
            context.log("هیچ عکسی دانلود نشد – fallback استفاده شد.")
            final_image_url = "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=512&h=512&fit=crop"

        # === ۶. ساخت data ===
        row_id = str(uuid.uuid4())

        data = {
            'title': trend_topic,
            'reportage_text': reportage_text,
            'status': 'ready_to_publish',
            'source_url': 'https://genshin.hoyoverse.com/en/news',
            'featured_media_url': 'https://www.youtube.com/watch?v=example_genshin_trailer',
            'hashtags': ['گیمینگ', 'بازی_موبایل', 'ترند', 'GenshinImpact']
        }

        if final_image_url and final_image_url.startswith('http'):
            data['image_url'] = final_image_url

        # === ۷. ذخیره در دیتابیس ===
        db.create_row(
            database_id=APPWRITE_DATABASE_ID,
            table_id=APPWRITE_COLLECTION_ID,
            row_id=row_id,
            data=data
        )
        context.log(f"مقاله با row_id: {row_id} ذخیره شد.")

        return context.res.json({
            "success": True,
            "message": "مقاله با عکس از وب آماده انتشار شد!",
            "row_id": row_id,
            "image_url": final_image_url
        })

    except Exception as e:
        context.error(f"خطای بحرانی: {str(e)}")
        return context.res.json({"success": False, "error": str(e)})
