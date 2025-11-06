import os
import asyncio
import requests
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.services.storage import Storage
from appwrite.query import Query
import uuid

async def main(context):
    context.log("فانکشن تحلیل ترند (با عکس از وب) شروع شد...")

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

        # === ۳. تولید ترند (مثال – بعداً با pytrends واقعی کن) ===
        trend_topic = "به‌روزرسانی جدید Genshin Impact"
        context.log(f"ترند پیدا شد: {trend_topic}")

        # === ۴. متن engaging پیش‌فرض (بدون AI – می‌تونی دستی تغییر بدی) ===
        reportage_text = f"🔥 {trend_topic}: بازی Genshin Impact با ویژگی‌های جدید مثل quests حماسی، گرافیک بهتر و ایونت‌های ویژه، گیمرها رو به هیجان می‌آره! آیا آماده‌ای برای ماجراجویی؟ 🎮 #GenshinImpact"
        context.log("متن engaging ساخته شد.")

        # === ۵. جستجو و دانلود عکس مرتبط از وب (رایگان، کم‌حجم) ===
        # جستجو در Pexels/Unsplash (رایگان، بدون API key – از RSS-like search)
        search_query = f"{trend_topic} mobile game wallpaper small"
        search_url = f"https://www.pexels.com/search/{search_query.replace(' ', '%20')}?auto=compress&cs=tinysrgb&w=512&h=512&fit=crop"
        
        # دانلود اولین عکس مرتبط (کم‌حجم: 512x512)
        img_response = requests.get(search_url)
        if img_response.status_code == 200:
            # استخراج لینک عکس از HTML (ساده – اولین img مرتبط)
            from bs4 import BeautifulSoup  # اگر requirements اضافه کن
            soup = BeautifulSoup(img_response.text, 'html.parser')
            img_tag = soup.find('img', {'src': True, 'alt': lambda x: x and 'genshin' in x.lower() if x else False})
            if img_tag:
                img_src = img_tag['src']
                if not img_src.startswith('http'):
                    img_src = 'https://www.pexels.com' + img_src
                img_data = requests.get(img_src, params={'w': 512, 'h': 512}).content  # کم‌حجم
                context.log(f"عکس از وب دانلود شد: {img_src}")
            else:
                img_data = None
                context.log("عکس مرتبط پیدا نشد – fallback استفاده شد.")
        else:
            img_data = None
            context.log("جستجو شکست خورد.")

        final_image_url = None
        if img_data:
            # آپلود به Appwrite Storage
            uploaded = storage.create_file(
                bucket_id=APPWRITE_BUCKET_ID,
                file_id='unique()',
                file=img_data,
                filename=f"{trend_topic.replace(' ', '_')}_lowres.png"
            )
            final_image_url = f"https://cloud.appwrite.io/v1/storage/buckets/{APPWRITE_BUCKET_ID}/files/{uploaded['$id']}/view?project={APPWRITE_PROJECT_ID}"
            context.log(f"عکس کم‌حجم آپلود شد: {final_image_url}")

        # fallback اگر دانلود نشد (لینک مستقیم کم‌حجم از Pexels)
        if not final_image_url:
            final_image_url = "https://images.pexels.com/photos/1542751/pexels-photo-1542751.jpeg?w=512&h=512&fit=crop"  # عکس گیمینگ عمومی، کم‌حجم

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

        # فقط لینک معتبر ذخیره کن
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
