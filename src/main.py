# --- شروع اسکریپت Trend-Analyzer (نسخه بهبودیافته و پایدار) ---

import os
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases  # استفاده از کلاس سازگار
from appwrite.services.storage import Storage
from appwrite.exception import AppwriteException  # برای مدیریت خطاهای Appwrite
from appwrite.query import Query
from appwrite.id import ID  # برای ساخت IDهای یونیک
from appwrite.input_file import InputFile

# تابع اصلی به حالت همزمان (sync) برگشت تا با کد requests سازگار باشد
def main(context):
    context.log("فانکشن تحلیل ترند (نسخه بهبودیافته) شروع شد...")

    try:
        # === ۱. دریافت متغیرها ===
        APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")
        APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
        APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
        APPWRITE_DATABASE_ID = os.environ.get("APPWRITE_DATABASE_ID")
        APPWRITE_COLLECTION_ID = os.environ.get("APPWRITE_COLLECTION_ID")
        APPWRITE_BUCKET_ID = os.environ.get("APPWRITE_BUCKET_ID", "images") # استفاده از مقدار پیش‌فرض "images"

        # === ۲. تنظیم کلاینت Appwrite ===
        client = Client()
        client.set_endpoint(APPWRITE_ENDPOINT)
        client.set_project(APPWRITE_PROJECT_ID)
        client.set_key(APPWRITE_API_KEY)
        db = Databases(client)  # استفاده از کلاس سازگار
        storage = Storage(client)
        context.log("کلاینت Appwrite آماده شد.")

        # === ۳. چک و ساخت Bucket (با مدیریت خطای دقیق) ===
        try:
            storage.get_bucket(APPWRITE_BUCKET_ID)
            context.log(f"Bucket '{APPWRITE_BUCKET_ID}' موجود است.")
        except AppwriteException as e:
            # اگر خطا "bucket_not_found" بود، آن را بساز
            if e.code == 404: 
                context.log(f"Bucket '{APPWRITE_BUCKET_ID}' یافت نشد، در حال ساخت...")
                storage.create_bucket(
                    bucket_id=APPWRITE_BUCKET_ID,
                    name="Images for Posts",
                    permissions=["read(\"any\")"] # فقط دسترسی خواندن عمومی می‌دهیم
                )
                context.log(f"Bucket '{APPWRITE_BUCKET_ID}' ساخته شد.")
            else:
                # اگر خطا چیز دیگری بود، آن را نمایش بده
                raise e

        # === ۴. تولید ترند (موقت برای تست) ===
        trend_topic = "به‌روزرسانی جدید Genshin Impact"
        context.log(f"ترند پیدا شد: {trend_topic}")

        # === ۵. متن engaging (موقت برای تست) ===
        reportage_text = f"{trend_topic}: بازی Genshin Impact با ویژگی‌های جدید مثل quests حماسی، گرافیک بهتر و ایونت‌های ویژه، گیمرها رو به هیجان می‌آره! آیا آماده‌ای برای ماجراجویی؟ #GenshinImpact"
        context.log("متن engaging ساخته شد.")

        # === ۶. دانلود عکس از وب ===
        possible_images = [
            "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=512&h=512&fit=crop",
            "https://wallpaperaccess.com/full/1668x2224.jpg?w=512&h=512&fit=crop"
        ]

        img_data = None
        for img_url in possible_images:
            try:
                img_response = requests.get(img_url, timeout=10) # افزایش زمان timeout به ۱۰ ثانیه
                if img_response.status_code == 200:
                    img_data = img_response.content
                    context.log(f"عکس دانلود شد (حجم: {len(img_data)} bytes)")
                    break
            except Exception as e:
                context.log(f"خطای دانلود عکس: {str(e)}")
                continue

        final_image_url = None
        if img_data:
            uploaded = storage.create_file(
                bucket_id=APPWRITE_BUCKET_ID,
                file_id=ID.unique(), # استفاده از روش استاندارد
                file=InputFile.from_bytes(img_data, "image.png")
            )
            # ساخت URL کامل برای مشاهده فایل
            final_image_url = f"{APPWRITE_ENDPOINT}/storage/buckets/{APPWRITE_BUCKET_ID}/files/{uploaded['$id']}/view?project={APPWRITE_PROJECT_ID}"
            context.log(f"عکس آپلود شد: {final_image_url}")
        else:
            final_image_url = "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=512&h=512&fit=crop" # عکس جایگزین

        # === ۷. ذخیره در دیتابیس (با متدهای سازگار v11) ===
        data = {
            'title': trend_topic,
            'reportage_text': reportage_text,
            'status': 'ready_to_publish',
            'source_url': 'https://genshin.hoyov-erse.com/en/news',
            'featured_media_url': 'https://www.youtube.com/watch?v=example_genshin_trailer',
            'hashtags': ['گیمینگ', 'بازی_موبایل', 'ترند', 'GenshinImpact'],
            'image_url': final_image_url # ستون جدیدی که ساختیم
        }

        # استفاده از create_document (سازگار با SDK نصب شده)
        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID,
            document_id=ID.unique(), # استفاده از روش استاندارد
            data=data
        )
        context.log(f"مقاله با document_id: {doc['$id']} ذخیره شد.")

        return context.res.json({
            "success": True,
            "message": "مقاله آماده انتشار شد!",
            "document_id": doc['$id'],
            "image_url": final_image_url
        })

    except Exception as e:
        context.error(f"خطای بحرانی: {str(e)}")
        return context.res.json({"success": False, "error": str(e)})
