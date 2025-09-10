import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    JobQueue,
)
import datetime
import json
import os

# تنظیمات اولیه
TOKEN = "8091231817:AAFa_1XqxVnyQ5Dc3FjTvxGnKmgg9_mr58o"
ADMIN_CHAT_ID = [508332264, 1141166768]  # لیست ادمین‌ها
BOT_USERNAME = "@MyServiceSupport1"  # آیدی ربات شما

# مراحل گفتگو
SELECT_SERVICE, PAYMENT_METHOD, RECEIPT_PHOTO, DISCOUNT_CODE = range(4)

# لیست سرویس‌ها با اطلاعات کامل
SERVICES = [
    {
        "name": "1 ماهه - 1 کاربره", 
        "price": 89000, 
        "duration": "1 ماه", 
        "days": 30, 
        "volume": "🌐 نامحدود",
        "emoji": "🔵",
        "description": "سرویس یک ماهه با حجم نامحدود"
    },
    {
        "name": "3 ماهه - 1 کاربره", 
        "price": 249000, 
        "duration": "3 ماه", 
        "days": 90, 
        "volume": "🌐 نامحدود",
        "emoji": "🟢",
        "description": "سرویس سه ماهه با حجم نامحدود"
    },
    {
        "name": "6 ماهه - 1 کاربره", 
        "price": 459000, 
        "duration": "6 ماه", 
        "days": 180, 
        "volume": "🌐 نامحدود",
        "emoji": "🟠",
        "description": "سرویس شش ماهه با حجم نامحدود"
    },
]

# کدهای تخفیف
DISCOUNT_CODES = {
    "312": {
        "discount": 0.1,  # 10% تخفیف
        "card_index": 0  # استفاده از کارت آرمین ختایی
    },
    "311": {
        "discount": 0.15,  # 15% تخفیف
        "card_index": 1  # استفاده از کارت محمد رضا صابون چی
    }
}

# اطلاعات کارت‌ها
CARDS = [
    {
        "number": "5859831146061881",
        "name": "آرمین ختایی",
        "emoji": "💳"
    },
    {
        "number": "6037998194751234", 
        "name": "محمد رضا صابون چی",
        "emoji": "💳"
    }
]

# دیکشنری برای ذخیره انتخاب‌های کاربران
user_data = {}

# دیکشنری برای ذخیره آخرین کارت استفاده شده توسط هر کاربر
user_last_card = {}

# دیکشنری برای ذخیره ID پیام‌های کارت‌های هر کاربر
user_card_messages = {}

# فایل دیتابیس برای ذخیره سرویس‌های کاربران
USER_SERVICES_FILE = "user_services.json"

def load_user_services():
    """بارگذاری سرویس‌های کاربران از فایل"""
    if os.path.exists(USER_SERVICES_FILE):
        try:
            with open(USER_SERVICES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_services(data):
    """ذخیره سرویس‌های کاربران در فایل"""
    with open(USER_SERVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# بارگذاری دیتابیس
user_services_db = load_user_services()

def add_bot_signature(text: str) -> str:
    """اضافه کردن امضای ربات به متن"""
    return f"{text}\n\n🤖 {BOT_USERNAME}" if BOT_USERNAME not in text else text

def get_main_menu():
    """تابع برای ایجاد منوی اصلی"""
    keyboard = [
        [KeyboardButton("✨ خرید سرویس ✨")],
        [KeyboardButton("🎯 تست رایگان 🎯"), KeyboardButton("📋 سرویس‌ها 📋")],
        [KeyboardButton("📊 سرویس من 📊"), KeyboardButton("🛟 پشتیبانی 🛟")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def show_main_menu(update: Update, message: str = None):
    """نمایش منوی اصلی با پیام دلخواه"""
    if message is None:
        message = "لطفا از منوی زیر انتخاب کنید:"
    await update.message.reply_text(
        add_bot_signature(message),
        reply_markup=get_main_menu()
    )

async def send_service_activated_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    """ارسال پیام فعال شدن سرویس به کاربر با اطلاعات کامل"""
    try:
        # دریافت اطلاعات سرویس از دیتابیس
        user_id_str = str(user_id)
        if user_id_str in user_services_db:
            service = user_services_db[user_id_str]
            
            # محاسبه تاریخ انقضا
            activation_date = datetime.datetime.fromisoformat(service['activation_date'])
            expiration_date = activation_date + datetime.timedelta(days=service['days'])
            
            message = (
                f"✅ سرویس شما با مشخصات زیر فعال شد:\n\n"
                f"📦 نوع سرویس: {service['name']}\n"
                f"⏰ مدت زمان: {service['duration']}\n"
                f"👥 تعداد کاربر: 1 کاربره\n"
                f"🌐 حجم: {service.get('volume', 'نامحدود')}\n"
                f"💰 مبلغ پرداختی: {service['price']:,} تومان\n"
                f"📅 تاریخ فعال سازی: {activation_date.strftime('%Y/%m/%d %H:%M')}\n"
                f"📅 تاریخ انقضا: {expiration_date.strftime('%Y/%m/%d %H:%M')}\n\n"
                f"🎉 لذت ببرید از سرویس ما!"
            )
        else:
            message = (
                "✅ سرویس شما فعال شد\n\n"
                "🎉 لذت ببرید از سرویس ما!\n\n"
                "جهت تمدید یا خرید سرویس جدید دکمه خرید سرویس را بزنید"
            )
            
        await context.bot.send_message(
            chat_id=chat_id,
            text=add_bot_signature(message),
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logging.error(f"Error sending service activated message: {e}")

async def send_expiration_reminder(context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام یادآوری 1 روز قبل از اتمام سرویس"""
    job = context.job
    try:
        user_id = job.data["user_id"]
        chat_id = job.data["chat_id"]
        
        user_id_str = str(user_id)
        if user_id_str in user_services_db:
            service = user_services_db[user_id_str]
            
            if 'activation_date' in service:
                activation_date = datetime.datetime.fromisoformat(service['activation_date'])
                expiration_date = activation_date + datetime.timedelta(days=service['days'])
                remaining_time = expiration_date - datetime.datetime.now()
                
                # اگر دقیقاً 1 روز یا کمتر باقی مانده باشد
                if 0 < remaining_time.total_seconds() <= 86400:  # 1 روز = 86400 ثانیه
                    reminder_message = (
                        f"⏰ یادآوری مهم!\n\n"
                        f"فقط 1 روز تا پایان سرویس شما باقی مانده است.\n\n"
                        f"📦 سرویس: {service['name']}\n"
                        f"📅 تاریخ انقضا: {expiration_date.strftime('%Y/%m/%d %H:%M')}\n\n"
                        f"💡 جهت تمدید یا فعال سازی سرویس جدید، دکمه '✨ خرید سرویس ✨' را از منو انتخاب کنید.\n\n"
                        f"✅ از ادامه استفاده از خدمات ما لذت ببرید!"
                    )
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=add_bot_signature(reminder_message),
                        reply_markup=get_main_menu()
                    )
                    
    except Exception as e:
        logging.error(f"Error sending expiration reminder: {e}")

async def schedule_expiration_reminder(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int, service_days: int):
    """زمان‌بندی ارسال پیام یادآوری 1 روز قبل از اتمام سرویس"""
    try:
        # محاسبه زمان ارسال یادآوری (1 روز قبل از اتمام)
        reminder_time = (service_days - 1) * 86400  # ثانیه
        
        if reminder_time > 0:
            context.job_queue.run_once(
                send_expiration_reminder,
                reminder_time,
                data={
                    "user_id": user_id,
                    "chat_id": chat_id
                },
                name=f"expiration_reminder_{user_id}"
            )
            
    except Exception as e:
        logging.error(f"Error scheduling expiration reminder: {e}")

async def cleanup_user_data(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int):
    """پاک کردن داده‌های کاربر و بازگشت به منوی اصلی"""
    try:
        # پاک کردن داده‌های موقت کاربر
        if user_id in user_data:
            del user_data[user_id]
            
        # پاک کردن پیام‌های کارت کاربر بعد از 10 دقیقه
        if str(user_id) in user_card_messages:
            for message_id in user_card_messages[str(user_id)]:
                try:
                    await context.bot.delete_message(chat_id, message_id)
                except Exception as e:
                    logging.error(f"Error deleting card message: {e}")
            del user_card_messages[str(user_id)]
            
        # ارسال پیام بازگشت به منوی اصلی
        await context.bot.send_message(
            chat_id,
            add_bot_signature("⏰ زمان پرداخت شما به پایان رسید. لطفا از منوی زیر انتخاب کنید:"),
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logging.error(f"Error in cleanup_user_data: {e}")

async def delete_card_messages_after_delay(context: ContextTypes.DEFAULT_TYPE):
    """حذف پیام‌های کارت بعد از 10 دقیقه"""
    job = context.job
    try:
        user_id = job.data["user_id"]
        chat_id = job.data["chat_id"]
        
        # پاک کردن پیام‌های کارت کاربر بعد از 10 دقیقه
        if str(user_id) in user_card_messages:
            for message_id in user_card_messages[str(user_id)]:
                try:
                    await context.bot.delete_message(chat_id, message_id)
                except Exception as e:
                    logging.error(f"Error deleting card message: {e}")
            del user_card_messages[str(user_id)]
            
    except Exception as e:
        logging.error(f"Error in delete_card_messages_after_delay: {e}")

async def delete_payment_message(context: ContextTypes.DEFAULT_TYPE):
    """حذف پیام پرداخت بعد از زمان مشخص و بازگشت به منوی اصلی"""
    job = context.job
    try:
        # حذف پیام پرداخت
        await context.bot.delete_message(job.chat_id, job.data["message_id"])
        
        # تمیز کردن داده‌های کاربر و بازگشت به منوی اصلی
        await cleanup_user_data(context, job.data["user_id"], job.chat_id)
            
    except Exception as e:
        logging.error(f"Error deleting message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع گفتگو و نمایش منوی اصلی"""
    user = update.effective_user
    
    # پاک کردن داده‌های موقت کاربر هنگام شروع مجدد
    if user.id in user_data:
        del user_data[user.id]
    
    # لغو تمام jobهای مربوط به این کاربر
    current_jobs = context.job_queue.get_jobs_by_name(f"payment_timeout_{user.id}")
    for job in current_jobs:
        job.schedule_removal()
    
    # لغو jobهای حذف کارت
    current_card_jobs = context.job_queue.get_jobs_by_name(f"card_delete_{user.id}")
    for job in current_card_jobs:
        job.schedule_removal()
    
    welcome_message = (
        "🌟 سلام به ربات BestVpn خوش آمدید 🌟\n\n"
        "🛡️ ارائه دهنده سرویس‌های VPN پرسرعت و مطمئن\n\n"
        "✅ ویژگی‌های سرویس‌های ما:\n"
        "• 🔒 امنیت و حریم خصوصی\n"
        "• 🚀 سرعت بالا و پینگ پایین\n"
        "• 🌐 حجم نامحدود اینترنت\n"
        "• 📱 سازگاری با تمام دستگاه‌ها\n\n"
        "جهت خرید فیلترشکن (VPN) از ربات لطفا روی گزینه '✨ خرید سرویس ✨' کلیک کنید."
    )
    
    await update.message.reply_text(
        add_bot_signature(welcome_message),
        reply_markup=get_main_menu()
    )
    return SELECT_SERVICE

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال اطلاعات پشتیبانی"""
    support_text = (
        "🛟 پشتیبانی آنلاین\n\n"
        "📞 برای ارتباط با پشتیبانی به آیدی زیر پیام دهید:\n"
        "👉 @PolotoCall\n\n"
        "⏰ ساعت پاسخگویی: 24 ساعته\n"
        "⚡ پاسخگویی سریع و مطمئن"
    )
    await update.message.reply_text(
        add_bot_signature(support_text),
        reply_markup=get_main_menu()
    )
    return SELECT_SERVICE

async def my_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش سرویس فعلی کاربر - نسخه بهبود یافته"""
    user = update.effective_user
    user_id_str = str(user.id)
    
    if user_id_str in user_services_db:
        service = user_services_db[user_id_str]
        
        # محاسبه روزهای باقی مانده
        if 'activation_date' in service:
            activation_date = datetime.datetime.fromisoformat(service['activation_date'])
            expiration_date = activation_date + datetime.timedelta(days=service['days'])
            remaining_time = expiration_date - datetime.datetime.now()
            
            if remaining_time.total_seconds() > 0:
                status = "✅ فعال"
                remaining_days = remaining_time.days
                remaining_hours = remaining_time.seconds // 3600
                remaining_text = f"⏳ {remaining_days} روز و {remaining_hours} ساعت باقی مانده"
            else:
                status = "❌ منقضی شده"
                remaining_text = "⏰ زمان سرویس به پایان رسیده است"
        else:
            status = "✅ فعال"
            remaining_text = "⏰ تاریخ شروع نامشخص"
        
        service_info = (
            f"📊 سرویس فعلی شما:\n\n"
            f"📦 نوع سرویس: {service['name']}\n"
            f"⏰ مدت زمان: {service['duration']}\n"
            f"👥 تعداد کاربر: 1 کاربره\n"
            f"🌐 حجم: {service.get('volume', 'نامحدود')}\n"
            f"💰 مبلغ پرداختی: {service['price']:,} تومان\n"
            f"📡 وضعیت: {status}\n"
            f"{remaining_text}\n\n"
        )
        
        if status == "✅ فعال":
            service_info += "🎉 از سرویس خود لذت ببرید!\n\n"
        else:
            service_info += "💡 برای تمدید سرویس، گزینه '✨ خرید سرویس ✨' را انتخاب کنید.\n\n"
            
        service_info += "برای تمدید یا خرید سرویس جدید، گزینه '✨ خرید سرویس ✨' را انتخاب کنید."
        
    else:
        service_info = (
            "📊 سرویس فعلی شما:\n\n"
            "❌ هیچ سرویس فعالی ندارید.\n\n"
            "💡 برای خرید سرویس جدید، گزینه '✨ خرید سرویس ✨' را انتخاب کنید."
        )
    
    await update.message.reply_text(
        add_bot_signature(service_info),
        reply_markup=get_main_menu()
    )
    return SELECT_SERVICE

async def free_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت درخواست تست رایگان"""
    user = update.effective_user
    
    # پیام به کاربر
    test_message = (
        "🎯 تست رایگان VPN\n\n"
        "✅ جهت دریافت تست رایگان لطفاً به یکی از آی‌دی‌های زیر پیام دهید:\n\n"
        "🔹 @MyServiceSupport1\n"
        "🔹 @MAMMAD\n\n"
        "⚡ دریافت کانفیگ تست در سریع‌ترین زمان ممکن"
    )
    
    await update.message.reply_text(
        add_bot_signature(test_message),
        reply_markup=get_main_menu()
    )
    
    # ارسال پیام به ادمین‌ها
    admin_message = (
        f"🎯 درخواست تست رایگان جدید\n\n"
        f"👤 کاربر: {user.first_name} {user.last_name or ''}\n"
        f"🆔 User ID: {user.id}\n"
        f"📞 یوزرنیم: @{user.username or 'ندارد'}\n\n"
        f"💬 برای ارسال کانفیگ تست از دستور زیر استفاده کنید:\n"
        f"/sendtest {user.id} <متن_کانفیگ_تست>\n\n"
        f"📝 یا ریپلای روی این پیام با دستور:\n"
        f"/sendtest <متن_کانفیگ_تست>"
    )
    
    for admin_id in ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message
            )
        except Exception as e:
            logging.error(f"Error sending message to admin {admin_id}: {e}")
    
    return SELECT_SERVICE

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش زیباتر لیست سرویس‌ها"""
    services_text = "📋 لیست سرویس‌های موجود:\n\n"
    
    for i, service in enumerate(SERVICES):
        services_text += (
            f"{service['emoji']} پلن {service['duration']}\n"
            f"💰 قیمت: {service['price']:,} تومان\n"
            f"👥 تعداد کاربر: 1 کاربره\n"
            f"🌐 حجم: {service['volume']}\n"
            f"⏰ مدت زمان: {service['duration']}\n"
            f"📝 {service['description']}\n"
        )
        
        if i < len(SERVICES) - 1:
            services_text += "\n" + "─" * 30 + "\n\n"
    
    await update.message.reply_text(
        add_bot_signature(services_text),
        reply_markup=get_main_menu()
    )
    return SELECT_SERVICE

async def select_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پردازش انتخاب سرویس - نسخه بهبود یافته"""
    text = update.message.text
    
    if text == "🛟 پشتیبانی 🛟":
        return await support(update, context)
    
    if text == "📊 سرویس من 📊":
        return await my_service(update, context)
    
    if text == "🎯 تست رایگان 🎯":
        return await free_test(update, context)
    
    if text == "📋 سرویس‌ها 📋":
        return await show_services(update, context)
    
    if text == "✨ خرید سرویس ✨":
        # نمایش سرویس‌های قابل خرید به صورت زیباتر
        services_text = "🌟 سرویس‌های قابل خرید:\n\n"
        
        for i, service in enumerate(SERVICES):
            services_text += (
                f"{service['emoji']} {service['name']}\n"
                f"💰 {service['price']:,} تومان\n"
                f"🌐 حجم: {service['volume']}\n"
                f"⏰ مدت: {service['duration']}\n\n"
            )
        
        # ایجاد کیبورد برای انتخاب سرویس
        keyboard = []
        for service in SERVICES:
            keyboard.append([KeyboardButton(f"{service['emoji']} {service['name']} - {service['price']:,} تومان")])
        keyboard.append([KeyboardButton("🔙 بازگشت 🔙")])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            add_bot_signature(services_text),
            reply_markup=reply_markup
        )
        
        return PAYMENT_METHOD
    
    elif text == "🔙 بازگشت 🔙":
        return await start(update, context)
    
    # بررسی انتخاب سرویس از دکمه‌های جدید
    selected_service = None
    for service in SERVICES:
        if f"{service['emoji']} {service['name']} - {service['price']:,} تومان" in text:
            selected_service = service
            break
    
    if selected_service:
        # ذخیره انتخاب пользователя
        if update.effective_user.id not in user_data:
            user_data[update.effective_user.id] = {}
            
        user_data[update.effective_user.id]["service"] = selected_service
        user_data[update.effective_user.id]["chat_id"] = update.message.chat_id
        
        # نمایش اطلاعات سرویس انتخاب شده
        service_info = (
            f"✅ سرویس انتخاب شده:\n\n"
            f"{selected_service['emoji']} {selected_service['name']}\n"
            f"💰 قیمت: {selected_service['price']:,} تومان\n"
            f"👥 تعداد کاربر: 1 کاربره\n"
            f"🌐 حجم: {selected_service['volume']}\n"
            f"⏰ مدت زمان: {selected_service['duration']}\n\n"
            f"لطفا روش پرداخت را انتخاب کنید:"
        )
        
        keyboard = [
            [KeyboardButton("💳 کارت به کارت 💳")],
            [KeyboardButton("🎫 استفاده از کد تخفیف 🎫")],
            [KeyboardButton("🔙 بازگشت 🔙")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            add_bot_signature(service_info),
            reply_markup=reply_markup
        )
        
        return PAYMENT_METHOD
    
    else:
        await show_main_menu(update)
        return SELECT_SERVICE

async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """انتخاب روش پرداخت - نسخه بهبود یافته"""
    text = update.message.text
    user = update.effective_user
    
    if text == "🛟 پشتیبانی 🛟":
        return await support(update, context)
    
    if text == "🎫 استفاده از کد تخفیف 🎫":
        await update.message.reply_text(
            "🎫 کد تخفیف خود را وارد کنید:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 بازگشت 🔙")]], resize_keyboard=True)
        )
        return DISCOUNT_CODE
    
    if text == "💳 کارت به کارت 💳":
        # بررسی وجود سرویس انتخاب شده
        if user.id not in user_data or 'service' not in user_data[user.id]:
            await update.message.reply_text(
                "❌ ابتدا یک سرویس را انتخاب کنید.",
                reply_markup=get_main_menu()
            )
            return SELECT_SERVICE
            
        service = user_data[user.id]['service']
        price = user_data[user.id].get('discounted_price', service['price'])
        
        # نمایش اطلاعات کامل سرویس
        service_info = (
            f"📦 سرویس انتخابی:\n"
            f"• {service['name']}\n"
            f"• حجم: {service['volume']}\n"
            f"• مدت: {service['duration']}\n"
            f"• کاربر: 1 کاربره\n\n"
        )
        
        # بررسی اینکه آیا کاربر قبلاً پرداختی داشته یا نه
        user_id_str = str(user.id)
        
        # اگر کاربر اولین پرداختش است یا قبلاً کارتی انتخاب نکرده
        if user_id_str not in user_last_card:
            # نمایش هر دو کارت برای اولین پرداخت
            card_message = (
                f"💳 {CARDS[0]['number']}\n"
                f"👨🏻‍💻 به نام: {CARDS[0]['name']}\n\n"
                f"💳 {CARDS[1]['number']}\n"
                f"👨🏻‍💻 به نام: {CARDS[1]['name']}\n\n"
            )
            payment_message = (
                f"✅ لطفاً مبلغ {price:,} تومان را به یکی از شماره کارت‌های زیر پرداخت کنید:\n\n"
                + service_info
                + card_message
            )
        else:
            # استفاده از کارت قبلی کاربر برای پرداخت‌های بعدی
            card_index = user_last_card[user_id_str]
            card_info = CARDS[card_index]
            card_message = f"💳 {card_info['number']}\n👨🏻‍💻 به نام: {card_info['name']}\n\n"
            payment_message = (
                f"✅ لطفاً مبلغ {price:,} تومان را به شماره کارت زیر پرداخت کنید:\n\n"
                + service_info
                + card_message
            )
        
        payment_message += (
            f"⏳ این تراکنش فقط تا 10 دقیقه مهلت پرداخت دارد.\n\n"
            f"لطفاً پس از پرداخت، تصویر رسید را ارسال کنید."
        )
        
        sent_message = await update.message.reply_text(
            add_bot_signature(payment_message),
            reply_markup=ReplyKeyboardRemove()
        )
        
        # ذخیره ID پیام کارت برای کاربر
        if str(user.id) not in user_card_messages:
            user_card_messages[str(user.id)] = []
        user_card_messages[str(user.id)].append(sent_message.message_id)
        
        # زمان‌بندی حذف پیام پرداخت بعد از 10 دقیقه (600 ثانیه)
        context.job_queue.run_once(
            delete_payment_message, 
            600,  # 10 دقیقه
            chat_id=update.message.chat_id,
            data={
                "message_id": sent_message.message_id,
                "user_id": user.id,
                "receipt_received": False
            },
            name=f"payment_timeout_{user.id}"
        )
        
        # زمان‌بندی حذف پیام کارت بعد از 10 دقیقه
        context.job_queue.run_once(
            delete_card_messages_after_delay, 
            600,  # 10 دقیقه
            chat_id=update.message.chat_id,
            data={
                "user_id": user.id,
                "chat_id": update.message.chat_id
            },
            name=f"card_delete_{user.id}"
        )
        
        return RECEIPT_PHOTO
    
    # پیدا کردن سرویس انتخاب شده
    selected_service = None
    for service in SERVICES:
        if f"{service['emoji']} {service['name']} - {service['price']:,} تومان" in text:
            selected_service = service
            break
    
    if selected_service:
        # ذخیره انتخاب کاربر
        if user.id not in user_data:
            user_data[user.id] = {}
            
        user_data[user.id]["service"] = selected_service
        user_data[user.id]["chat_id"] = update.message.chat_id
        
        keyboard = [
            [KeyboardButton("💳 کارت به کارت 💳")],
            [KeyboardButton("🎫 استفاده از کد تخفیف 🎫")],
            [KeyboardButton("🔙 بازگشت 🔙")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        service_info = (
            f"🌟 سرویس انتخاب شده:\n\n"
            f"{selected_service['emoji']} {selected_service['name']}\n"
            f"💰 قیمت: {selected_service['price']:,} تومان\n"
            f"👥 تعداد کاربر: 1 کاربره\n"
            f"🌐 حجم: {selected_service['volume']}\n"
            f"⏰ مدت زمان: {selected_service['duration']}\n\n"
            "📢 همین الان اگه کد تخفیف داری روی دکمه‌ی «🎫 استفاده از کد تخفیف 🎫» بزن تا تخفیف اعمال بشه، در غیر این صورت با رفتن به مرحله بعد کدت می‌سوزه و باطل میشه."
        )
        
        await update.message.reply_text(
            add_bot_signature(service_info),
            reply_markup=reply_markup
        )
        
        return PAYMENT_METHOD
    
    elif text == "🔙 بازگشت 🔙":
        return await start(update, context)
    
    else:
        await show_main_menu(update)
        return PAYMENT_METHOD

async def handle_discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پردازش کد تخفیف"""
    text = update.message.text
    user = update.effective_user
    
    if text == "🔙 بازگشت 🔙":
        return await payment_method(update, context)
    
    if text in DISCOUNT_CODES:
        # بررسی وجود سرویس انتخاب شده
        if user.id not in user_data or 'service' not in user_data[user.id]:
            await update.message.reply_text(
                "ابتدا یک سرویس را انتخاب کنید.",
                reply_markup=get_main_menu()
            )
            return SELECT_SERVICE
            
        discount_info = DISCOUNT_CODES[text]
        original_price = user_data[user.id]['service']['price']
        discounted_price = int(original_price * (1 - discount_info['discount']))
        card_info = CARDS[discount_info['card_index']]
        
        user_data[user.id]['discounted_price'] = discounted_price
        user_data[user.id]['discount_code'] = text
        
        # ذخیره کارت استفاده شده برای کاربر
        user_id_str = str(user.id)
        user_last_card[user_id_str] = discount_info['card_index']
        
        payment_message = (
            f"✅ کد تخفیف اعمال شد!\n\n"
            f"💰 قیمت اصلی: {original_price:,} تومان\n"
            f"🎫 قیمت با تخфиف: {discounted_price:,} تومان\n"
            f"💸 صرفه‌جویی: {original_price - discounted_price:,} تومان\n\n"
            f"لطفاً مبلغ {discounted_price:,} تومان را به شماره کارت زیر پرداخت کنید:\n\n"
            f"💳 {card_info['number']}\n"
            f"👨🏻‍💻 به نام: {card_info['name']}\n\n"
            f"⏳ این تراکنش فقط تا 10 دقیقه مهلت پرداخت دارد.\n\n"
            f"لطفاً پس از پرداخت، تصویر رسید را ارسال کنید."
        )
        
        sent_message = await update.message.reply_text(
            add_bot_signature(payment_message),
            reply_markup=ReplyKeyboardRemove()
        )
        
        # ذخیره ID پیام کارت برای کاربر
        if str(user.id) not in user_card_messages:
            user_card_messages[str(user.id)] = []
        user_card_messages[str(user.id)].append(sent_message.message_id)
        
        # زمان‌بندی حذف پیام پرداخت بعد از 10 دقیقه
        context.job_queue.run_once(
            delete_payment_message, 
            600,  # 10 دقیقه
            chat_id=update.message.chat_id,
            data={
                "message_id": sent_message.message_id,
                "user_id": user.id,
                "receipt_received": False
            },
            name=f"payment_timeout_{user.id}"
        )
        
        # زمان‌بندی حذف پیام کارت بعد از 10 دقیقه
        context.job_queue.run_once(
            delete_card_messages_after_delay, 
            600,  # 10 دقیقه
            chat_id=update.message.chat_id,
            data={
                "user_id": user.id,
                "chat_id": update.message.chat_id
            },
            name=f"card_delete_{user.id}"
        )
        
        return RECEIPT_PHOTO
    else:
        await update.message.reply_text(
            "❌ کد تخفیف نامعتبر است. لطفا دوباره امتحان کنید یا از گزینه بازگشت استفاده کنید.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 بازگشت 🔙")]], resize_keyboard=True)
        )
        return DISCOUNT_CODE

async def receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت عکس رسید پرداخت"""
    user = update.effective_user
    text = update.message.text if update.message.text else ""
    
    # لغو job حذف پیام پرداخت (کاربر رسید ارسال کرده)
    current_jobs = context.job_queue.get_jobs_by_name(f"payment_timeout_{user.id}")
    for job in current_jobs:
        job.schedule_removal()
    
    # اگر کاربر از منو استفاده کرد (عکس نفرستاد)
    if not update.message.photo and text in ["✨ خرید سرویس ✨", "🎯 تست رایگان 🎯", "📋 سرویس‌ها 📋", "📊 سرویس من 📊", "🛟 پشتیبانی 🛟", "🔙 بازگشت 🔙"]:
        # پاک کردن داده‌های موقت کاربر
        if user.id in user_data:
            del user_data[user.id]
        
        # بازگشت به منوی اصلی
        await show_main_menu(update, "❌ پرداخت شما لغو شد. لطفا از منوی زیر انتخاب کنید:")
        return SELECT_SERVICE
    
    if update.message.photo:
        # ذخیره اطلاعات کاربر اگر وجود ندارد
        if user.id not in user_data:
            user_data[user.id] = {
                "service": {"name": "نامشخص", "price": 0, "duration": "نامشخص"},
                "chat_id": update.message.chat_id
            }
        
        photo = update.message.photo[-1]  # گرفتن بالاترین رزولوشن عکس
        
        # ذخیره سرویس در دیتابیس
        user_id = str(user.id)
        service_data = user_data[user.id]['service'].copy()
        
        # اضافه کردن اطلاعات کامل سرویس
        for service in SERVICES:
            if service['name'] == service_data['name']:
                service_data.update(service)
                break
        
        # اضافه کردن تاریخ فعال شدن
        service_data['activation_date'] = datetime.datetime.now().isoformat()
        
        # ذخیره اطلاعات کارت استفاده شده اگر وجود دارد
        if 'selected_card' in user_data[user.id]:
            user_last_card[user_id] = user_data[user.id]['selected_card']
            service_data['selected_card'] = user_data[user.id]['selected_card']
        
        user_services_db[user_id] = service_data
        save_user_services(user_services_db)
        
        # زمان‌بندی ارسال پیام یادآوری 1 روز قبل از اتمام
        await schedule_expiration_reminder(context, user.id, update.message.chat_id, service_data['days'])
        
        # پیام به ادمین‌ها
        admin_message = (
            f"📨 رسید پرداخت جدید\n"
            f"👤 کاربر: @{user.username or 'ندارد'} ({user.first_name} {user.last_name or ''})\n"
            f"🆔 چت آیدی: {user.id}\n"
            f"📌 سرویس: {user_data[user.id]['service']['name']}\n"
            f"💰 مبلغ اصلی: {user_data[user.id]['service']['price']:,} تومان"
        )
        
        if 'discount_code' in user_data.get(user.id, {}):
            admin_message += (
                f"\n🎫 کد تخفیف: {user_data[user.id]['discount_code']}\n"
                f"💲 مبلغ با تخفیف: {user_data[user.id]['discounted_price']:,} تومان\n"
                f"💳 کارت انتخابی: {CARDS[user_last_card[str(user.id)]]['number']}"
            )
        else:
            # اگر کاربر از کد تخفیف استفاده نکرده، از کارت قبلی یا کارت اول استفاده کن
            card_index = user_last_card.get(str(user.id), 0)
            admin_message += f"\n💳 کارت انتخابی: {CARDS[card_index]['number']}"
        
        # ارسال عکس رسید به همه ادمین‌ها
        for admin_id in ADMIN_CHAT_ID:
            try:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=photo.file_id,
                    caption=admin_message
                )
            except Exception as e:
                logging.error(f"Error sending photo to admin {admin_id}: {e}")
        
        # پاسخ به کاربر
        await update.message.reply_text(
            add_bot_signature(
                "✅ رسید شما دریافت شد.\n"
                "پس از تأیید پرداخت، کانفیگ سرویس برای شما ارسال خواهد شد.\n\n"
                "⏳ زمان تحویل کانفیگ: ۵ تا ۱۰ دقیقه"
            ),
            reply_markup=get_main_menu()
        )
        
        # پاک کردن داده‌های موقت کاربر
        if user.id in user_data:
            del user_data[user.id]
        
        return SELECT_SERVICE
    
    else:
        # اگر کاربر متنی غیر از منو ارسال کرد
        await update.message.reply_text(
            add_bot_signature("لطفا فقط تصویر رسید پرداخت را ارسال کنید یا از منوی زیر استفاده کنید:"),
            reply_markup=get_main_menu()
        )
        return RECEIPT_PHOTO

async def send_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور برای ارسال کانفیگ به کاربر توسط ادمین"""
    user = update.effective_user
    
    # بررسی اینکه آیا کاربر ادمین است
    if user.id not in ADMIN_CHAT_ID:
        await update.message.reply_text(add_bot_signature("⛔ دسترسی غیرمجاز!"))
        return
    
    # بررسی ساختار دستور
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            add_bot_signature(
                "⚠️ فرمت دستور نادرست است.\n"
                "استفاده صحیح:\n"
                "روش 1: /sendconfig <چت_آیدی> <متن_کانفیگ>\n"
                "روش 2: /sendconfig\n<چت_آیدی>\n<متن_کانفیگ>\n"
                "روش 3: ریپلای روی رسید کاربر با /sendconfig <متن_کانفیگ>"
            )
        )
        return
    
    try:
        target_user_id = None
        
        # اگر ریپلای روی رسید کاربر باشد
        if update.message.reply_to_message:
            reply_msg = update.message.reply_to_message
            if reply_msg.caption and "چت آیدی:" in reply_msg.caption:
                # استخراج چت آیدی از پیام ریپلای شده
                chat_id_line = [line for line in reply_msg.caption.split('\n') if "چت آیدی:" in line][0]
                target_chat_id = int(chat_id_line.split(":")[1].strip())
                
                # استخراج user_id از پیام ریپلای شده
                user_id_line = [line for line in reply_msg.caption.split('\n') if "🆔 چت آیدی:" in line][0]
                target_user_id = int(user_id_line.split("🆔 چت آیدی:")[1].strip())
                
                # استخراج متن کانفیگ
                if context.args:
                    config_text = " ".join(context.args)
                else:
                    config_text = update.message.text.split("/sendconfig", 1)[1].strip()
            else:
                raise ValueError("پیام ریپلای شده معتبر نیست")
        else:
            # استخراج چت آیدی و متن کانفیگ از پیام
            message_text = update.message.text
            
            # روش 1: اگر چت آیدی در <> باشد
            if "<" in message_text and ">" in message_text:
                parts = message_text.split("<")[1].split(">")
                chat_id_part = parts[0].strip()
                config_text = ">".join(parts[1:]).strip()
                
                # اگر config_text با < شروع شود (روش ترکیبی)
                if "<" in config_text and ">" in config_text:
                    config_text = config_text.split("<")[1].split(">")[0].strip()
            else:
                # روش 2: فرمت استاندارد /sendconfig چت_آیدی متن_کانفیگ
                chat_id_part = context.args[0]
                config_text = " ".join(context.args[1:])
            
            # تبدیل چت آیدی به عدد
            target_chat_id = int(chat_id_part)
            target_user_id = target_chat_id  # در این حالت chat_id و user_id یکسان هستند
        
        # حذف کاراکترهای اضافی از متن کانفیگ
        config_text = config_text.strip()
        if config_text.startswith("<") and config_text.endswith(">"):
            config_text = config_text[1:-1].strip()
        
        # بررسی وجود متن کانفیگ
        if not config_text:
            raise ValueError("متن کانفیگ خالی است")
        
        # ارسال کانفیگ به کاربر
        await context.bot.send_message(
            chat_id=target_chat_id,
            text=add_bot_signature(f"🔑 کانفیگ سرویس شما:\n\n{config_text}\n\n✅ لذت ببرید!"),
            reply_markup=get_main_menu()
        )
        
        # ارسال پیام فعال شدن سرویس (اگر user_id مشخص است)
        if target_user_id:
            await send_service_activated_message(context, target_chat_id, target_user_id)
        else:
            await send_service_activated_message(context, target_chat_id, target_chat_id)
        
        # اطلاع به ادمین
        await update.message.reply_text(
            add_bot_signature(f"✅ کانفیگ با موفقیت برای کاربر با چت آیدی {target_chat_id} ارسال شد.")
        )
        
    except ValueError as ve:
        await update.message.reply_text(
            add_bot_signature(
                f"⚠️ خطا در پردازش دستور: {str(ve)}\n"
                "لطفاً مطمئن شوید چت آیدی یک عدد معتبر است و متن کانفیگ وجود دارد."
            )
        )
    except Exception as e:
        await update.message.reply_text(
            add_bot_signature(f"❌ خطا در ارسال کانفیگ: {str(e)}")
        )

async def send_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور برای ارسال کانفیگ تست به کاربر توسط ادمین"""
    user = update.effective_user
    
    # بررسی اینکه آیا کاربر ادمین است
    if user.id not in ADMIN_CHAT_ID:
        await update.message.reply_text(add_bot_signature("⛔ دسترسی غیرمجاز!"))
        return
    
    # بررسی ساختار دستور
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            add_bot_signature(
                "⚠️ فرمت دستور نادرست است.\n"
                "استفاده صحیح:\n"
                "روش 1: /sendtest <چت_آیدی> <متن_کانفیگ_تست>\n"
                "روش 2: /sendtest\n<چت_آیدی>\n<متن_کانفیگ_تست>\n"
                "روش 3: ریپلای روی پیام درخواست تست با /sendtest <متن_کانفیگ_تست>"
            )
        )
        return
    
    try:
        target_chat_id = None
        
        # اگر ریپلای روی پیام درخواست تست باشد
        if update.message.reply_to_message:
            reply_msg = update.message.reply_to_message
            if "User ID:" in reply_msg.text:
                # استخراج user_id از پیام ریپلای شده
                user_id_line = [line for line in reply_msg.text.split('\n') if "User ID:" in line][0]
                target_chat_id = int(user_id_line.split("User ID:")[1].strip())
                
                # استخراج متن کانفیگ تست
                if context.args:
                    config_text = " ".join(context.args)
                else:
                    config_text = update.message.text.split("/sendtest", 1)[1].strip()
            else:
                raise ValueError("پیام ریپلای شده معتبر نیست")
        else:
            # استخراج چت آیدی و متن کانفیگ تست از پیام
            message_text = update.message.text
            
            # روش 1: اگر چت آیدی در <> باشد
            if "<" in message_text and ">" in message_text:
                parts = message_text.split("<")[1].split(">")
                chat_id_part = parts[0].strip()
                config_text = ">".join(parts[1:]).strip()
                
                # اگر config_text با < شروع شود (روش ترکیبی)
                if "<" in config_text and ">" in config_text:
                    config_text = config_text.split("<")[1].split(">")[0].strip()
            else:
                # روش 2: فرمت استاندارد /sendtest چت_آیدی متن_کانفیگ_تست
                chat_id_part = context.args[0]
                config_text = " ".join(context.args[1:])
            
            # تبدیل چت آیدی به عدد
            target_chat_id = int(chat_id_part)
        
        # حذف کاراکترهای اضافی از متن کانفیگ تست
        config_text = config_text.strip()
        if config_text.startswith("<") and config_text.endswith(">"):
            config_text = config_text[1:-1].strip()
        
        # بررسی وجود متن کانفیگ تست
        if not config_text:
            raise ValueError("متن کانفیگ تست خالی است")
        
        # ارسال کانفیگ تست به کاربر
        test_message = add_bot_signature(
            f"🎉 کانفیگ تست رایگان شما:\n\n"
            f"{config_text}\n\n"
            f"⏰ مدت زمان تست: 24 ساعت\n"
            f"👥 تعداد کاربر: 1 کاربره\n"
            f"💾 حجم: 50 مگ\n\n"
            f"✅ لذت ببرید! در صورت رضایت می‌توانید سرویس کامل را خریداری کنید."
        )
        
        await context.bot.send_message(
            chat_id=target_chat_id,
            text=test_message,
            reply_markup=get_main_menu()
        )
        
        # اطلاع به ادمین
        await update.message.reply_text(
            add_bot_signature(f"✅ کانفیگ تست با موفقیت برای کاربر با چت آیدی {target_chat_id} ارسال شد.")
        )
        
    except ValueError as ve:
        await update.message.reply_text(
            add_bot_signature(
                f"⚠️ خطا در پردازش دستور: {str(ve)}\n"
                "لطفاً مطمئن شوید چت آیدی یک عدد معتبر است و متن کانفیگ تست وجود دارد."
            )
        )
    except Exception as e:
        await update.message.reply_text(
            add_bot_signature(f"❌ خطا در ارسال کانفیگ تست: {str(e)}")
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور راهنما"""
    user = update.effective_user
    
    if user.id in ADMIN_CHAT_ID:
        help_text = (
            "📌 دستورات ادمین:\n"
            "/sendconfig <چت_آیدی> <متن_کانفیگ> - ارسال کانفیگ به کاربر\n"
            "/sendtest <چت_آیدی> <متن_کانفیگ_تست> - ارسال کانفیگ تست\n"
            "یا ریپلای روی پیام کاربر با دستورات بالا\n\n"
            "📌 دستورات عمومی:\n"
            "/start - شروع کار با ربات\n"
            "/help - نمایش این راهنما"
        )
    else:
        help_text = (
            "📌 دستورات عمومی:\n"
            "/start - شروع کار با ربات\n"
            "/help - نمایش این راهنما\n\n"
            "پس از انتخاب سرویس و پرداخت، تصویر رسید را ارسال کنید."
        )
    
    await update.message.reply_text(
        add_bot_signature(help_text),
        reply_markup=get_main_menu()
    )

def main() -> None:
    """راه‌اندازی ربات"""
    application = Application.builder().token(TOKEN).build()
    
    # گفتگو برای خرید سرویس
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_service)
            ],
            PAYMENT_METHOD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, payment_method)
            ],
            DISCOUNT_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_discount_code)
            ],
            RECEIPT_PHOTO: [
                MessageHandler(filters.PHOTO, receipt_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receipt_photo)
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.Text(["🛟 پشتیبانی 🛟"]), support)
        ],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Text(["🛟 پشتیبانی 🛟"]), support))
    application.add_handler(MessageHandler(filters.Text(["🎯 تست رایگان 🎯"]), free_test))
    application.add_handler(MessageHandler(filters.Text(["📊 سرویس من 📊"]), my_service))
    application.add_handler(CommandHandler("sendconfig", send_config))
    application.add_handler(CommandHandler("sendtest", send_test))
    application.add_handler(CommandHandler("help", help_command))
    
    application.run_polling()

if __name__ == "__main__":
    main()
