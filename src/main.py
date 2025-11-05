# --- شروع اسکریپت Trend-Analyzer ---
# این فانکشن به گوگل ترندز متصل می‌شود، موضوعات داغ را پیدا می‌کند،
# و سپس از هوش مصنوعی Gemini برای تحلیل آن موضوع استفاده می‌کند.

import os
import asyncio
from pytrends.request import TrendReq
import google.generativeai as genai

# تابع اصلی ما اکنون باید به عنوان "async" (ناهمزمان) تعریف شود
async def main(context):
    context.log("فانکشن Trend-Analyzer شروع به کار کرد...")

    try:
        # ۱. دریافت کلید مخفی Google AI از متغیرهای پروژه
        GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
        if not GOOGLE_AI_API_KEY:
            context.log("خطا: GOOGLE_AI_API_KEY پیدا نشد.")
            return context.res.json({"success": False, "error": "API Key missing"})

        # ۲. تنظیم هوش مصنوعی Gemini
        genai.configure(api_key=GOOGLE_AI_API_KEY)
        
        # --- اصلاحیه اینجا اعمال شد ---
        # ما از مدل جدیدتر و سریع‌تر 'gemini-1.5-flash-latest' استفاده می‌کنیم
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        # --- پایان اصلاحیه ---
        
        context.log("هوش مصنوعی Gemini با موفقیت پیکربندی شد.")

        # ۳. اتصال به گوگل ترندز
        pytrends = TrendReq(hl='en-US', tz=360)
        # ما کلمات کلیدی اصلی صنعت خود را بررسی می‌کنیم
        keywords = ["mobile game", "genshin impact", "call of duty mobile", "pubg mobile"]
        pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='', gprop='')

        # ۴. دریافت موضوعات داغ مرتبط
        related_data = pytrends.related_topics()
        context.log("داده‌های گوگل ترندز دریافت شد.")

        # ۵. استخراج داغ‌ترین موضوع
        top_topic = "New update in mobile gaming" # موضوع نمونه
        
        # بررسی اینکه آیا دیتای مرتبطی وجود دارد یا خیر
        if keywords[0] in related_data and not related_data[keywords[0]]['rising'].empty:
            top_rising = related_data[keywords[0]]['rising']
            top_topic = top_rising.iloc[0]['topic_title']
        
        context.log(f"موضوع داغ شناسایی شده: {top_topic}")

        # ۶. ارسال موضوع به Gemini برای تحلیل و رپورتاژ
        prompt = (
            f"موضوع '{top_topic}' در حال حاضر در گوگل ترندز داغ است."
            "لطفاً به عنوان یک منتقد برتر بازی‌های موبایل، در اینترنت جستجو کن و یک «رپورتاژ» خلاقانه و دقیق به زبان فارسی بنویس."
            "این رپورتاژ باید شامل تحلیل، دلیل داغ شدن، و نقد کوتاه باشد."
            "همچنین، لطفاً بهترین لینک ویدیوی YouTube (تریلر یا گیم‌پلی) مرتبط با این موضوع را پیدا کن و فقط لینک خام آن را در انتهای پاسخ خود قرار بده."
        )
        
        # استفاده از generate_content_async برای اجرای ناهمزمان
        response = await model.generate_content_async(prompt)
        context.log("پاسخ از Gemini دریافت شد.")
        
        # ۷. پردازش پاسخ Gemini
        reportage_text = response.text
        
        context.log("--- نتیجه تحلیل هوش مصنوعی ---")
        context.log(reportage_text)
        context.log("---------------------------------")

        return context.res.json({"success": True, "topic": top_topic, "reportage_snippet": reportage_text[:150]})

    except Exception as e:
        context.error(f"خطای بحرانی در Trend-Analyzer رخ داد: {str(e)}")
        return context.res.json({"success": False, "error": str(e)})
