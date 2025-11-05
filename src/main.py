# --- شروع اسکریپت Trend-Analyzer (نسخه عیب‌یابی) ---
# هدف: پیدا کردن مدل‌های Gemini موجود برای این کلید API

import os
import google.generativeai as genai
import asyncio

# تابع اصلی ما اکنون باید به عنوان "async" (ناهمزمان) تعریف شود
async def main(context):
    context.log("فانکشن عیب‌یابی Trend-Analyzer شروع به کار کرد...")

    try:
        # ۱. دریافت کلید مخفی Google AI
        GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
        if not GOOGLE_AI_API_KEY:
            context.log("خطا: GOOGLE_AI_API_KEY پیدا نشد.")
            return context.res.json({"success": False, "error": "API Key missing"})

        # ۲. تنظیم هوش مصنوعی Gemini
        genai.configure(api_key=GOOGLE_AI_API_KEY)
        context.log("هوش مصنوعی Gemini با موفقیت پیکربندی شد.")

        # ۳. دریافت و لاگ کردن لیست تمام مدل‌های موجود
        context.log("--- شروع لیست مدل‌های موجود ---")
        
        # ما لیست مدل‌ها را می‌گیریم
        # این یک حلقه async نیست، پس مستقیم صدا می‌زنیم
        available_models = []
        for m in genai.list_models():
            # ما فقط مدل‌هایی را می‌خواهیم که از 'generateContent' پشتیبانی می‌کنند
            if 'generateContent' in m.supported_generation_methods:
                context.log(f"مدل موجود و قابل استفاده: {m.name}")
                available_models.append(m.name)
        
        context.log("--- پایان لیست مدل‌های موجود ---")
        
        if not available_models:
            context.log("هیچ مدل قابل استفاده‌ای (با generateContent) برای این کلید API یافت نشد.")
            
        return context.res.json({
            "success": True, 
            "message": "ListModels successful.", 
            "usable_models": available_models
        })

    except Exception as e:
        context.error(f"خطای بحرانی در Trend-Analyzer (عیب‌یابی) رخ داد: {str(e)}")
        return context.res.json({"success": False, "error": str(e)})
