import gspread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto,InlineKeyboardButton,InlineKeyboardMarkup
gc = gspread.service_account(filename='creds.json')
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters
)
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
import asyncio
import traceback
from logging.handlers import RotatingFileHandler








# تنظیمات اولیه
load_dotenv("config.env")

# تعریف حالت‌های گفتگو
(
    MAIN_MENU,
    WEBSITES_MENU,
    WEBSITE_CATEGORY,
    WEBSITE_ITEM,
    TELEGRAM_BOTS_MENU,
    TELEGRAM_BOT_DETAILS,
    REQUEST_BOT,
    WINDOWS_APPS_MENU,
    WINDOWS_APP_DETAILS,
    REQUEST_APP,
    SUPPORT_MENU,
    REQUEST_SUPPORT,
    ABOUT_MENU,
    FAVORITES_MENU,
    CONSULTATION,
    SERVICES_MENU,
    REQUEST_WEBSITE,
    COPY_NUMBER,
    SEARCH_ITEMS  

) = range(19)



# متن دکمه‌های منو
BTN_WEBSITES = "وب سایت‌ها 🌐"
BTN_TELEGRAM_BOTS = "ربات‌های تلگرام 🤖"
BTN_WINDOWS_APPS = "نرم‌افزارهای ویندوزی 💻"
BTN_SUPPORT = "پشتیبانی برای شما 🛠"
BTN_CONSULTATION = "درخواست و مشاوره 📩"
BTN_ABOUT = "درباره رادوتیم ℹ️"
BTN_FAVORITES = "لیست علاقه‌مندی‌ها ⭐"
BTN_SERVICES = "خدمات متنوع 🧰"
BTN_SEARCH = "جستجوی نمونه کارها 🔍"

BTN_ECOMMERCE = "فروشگاهی 🛒"
BTN_CORPORATE = "شرکتی 🏢"
BTN_RESUME = "رزومه 📄"
BTN_GALLERY = "گالری 🖼"
BTN_WEBSITE_PRICES = "هزینه‌های طراحی وب‌سایت 💰"
BTN_REQUEST_WEBSITE = "درخواست سایت 📩"
BTN_BACK_TO_MAIN = "منوی اصلی 🔙"

BTN_CONTACT = "📞 تماس با ما"
CONTACT_NUMBER = "09158708858"
# تنظیمات Google Sheets
logger = logging.getLogger(__name__)
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

try:
    logger.info("در حال خواندن فایل JSON...")
    creds = Credentials.from_service_account_file("radoteam-0da92609cd4a.json", scopes=scope)
    logger.info("اتصال به Google Sheets...")
    client = gspread.authorize(creds)
    logger.info("در حال باز کردن اسپردشیت...")
    sheet = client.open_by_key("1w7lQNjPnNR8lHBfneWOwQGSM3KCWtUSIPChH8l8R-xs")
    
    # دسترسی به شیت‌های مختلف
    sheet_mapping = {
        'websites': 'websites',
        'telegram_bots': 'telegramBots',
        'windows_apps': 'windowsApps',
        'support': 'support',
        'favorites': 'favorites',
        'services': 'services'
    }

    db = {}
    for key, sheet_name in sheet_mapping.items():
        try:
            logger.debug(f"در حال دسترسی به ورق '{sheet_name}'...")
            db[key] = sheet.worksheet(sheet_name)
            logger.info(f"✅ ورق '{sheet_name}' با موفقیت بارگذاری شد")
        except gspread.WorksheetNotFound:
            logger.error(f"❌ ورق '{sheet_name}' یافت نشد!")
            raise
        except Exception as e:
            logger.error(f"❌ خطا در بارگذاری ورق '{sheet_name}': {str(e)}")
            raise

except Exception as e:
    logger.critical(f"خطای بحرانی در اتصال به Google Sheets: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

# -------------------- توابع کمکی --------------------
def get_user_favorites(user_id):
    favorites = db["favorites"].get_all_records()
    return [fav for fav in favorites if str(fav["UserID"]) == str(user_id)]

def add_to_favorites(user_id, item_type, item_id):
    db["favorites"].append_row([user_id, item_type, item_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

def remove_from_favorites(user_id, item_type, item_id):
    favorites = db["favorites"].get_all_records()
    for i, fav in enumerate(favorites, start=2):
        if (str(fav["UserID"]) == str(user_id) and 
            fav["ItemType"] == item_type and 
            str(fav["ItemID"]) == str(item_id)):
            db["favorites"].delete_row(i)
            return True
    return False

def send_to_admin(context: CallbackContext, message):
    try:
        context.bot.send_message(
            chat_id=1810708143,  # اینجا UID ادمین را مستقیماً قرار دادیم
            text=message
        )
        logger.info("پیام با موفقیت به ادمین ارسال شد.")
    except Exception as e:
        logger.error(f"خطا در ارسال پیام به ادمین: {str(e)}")


# -------------------- دستور /start --------------------
async def start(update: Update, context: CallbackContext):
    user = update.message.from_user if update.message else update.callback_query.from_user
    contact_btn = KeyboardButton(BTN_CONTACT)
    
    keyboard = [
        [BTN_WEBSITES, BTN_TELEGRAM_BOTS],
        [BTN_WINDOWS_APPS, BTN_SUPPORT],
        [BTN_CONSULTATION, BTN_ABOUT],
        [BTN_FAVORITES, BTN_SERVICES],
        [contact_btn]  # اضافه کردن دکمه تماس
    ]
    
    welcome_text = f"""
✨ *سلام {user.first_name} عزیز!* ✨

⚡️ *به جمع مشتریان رادو تیم خوش آمدید!*

🚀 *خدمات ما:*
✅ طراحی وبسایت حرفه‌ای
✅ ساخت ربات تلگرام پیشرفته
✅ توسعه نرم‌افزارهای ویندوزی
✅ پشتیبانی و بهینه‌سازی


📌 *امکانات ربات:*
• مشاهده نمونه کارها
• دریافت مشاوره رایگان
• استعلام قیمت
• ارتباط مستقیم با تیم پشتیبانی

👇 برای شروع یکی از گزینه‌های زیر رو انتخاب کن:
"""
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    target = update.message if update.message else update.callback_query.message
    await target.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU



async def handle_contact_request(update: Update, context: CallbackContext):
    contact_keyboard = generate_contact_keyboard()
    
    reply_keyboard = ReplyKeyboardMarkup([[BTN_BACK_TO_MAIN]], resize_keyboard=True)
    
    await update.message.reply_text(
        f"📞 برای تماس با پشتیبانی:\n\n"
        f"شماره: <code>{CONTACT_NUMBER}</code>\n\n"
        "👉 می‌توانید از دکمه‌های زیر استفاده کنید:",
        parse_mode='HTML',
        reply_markup=contact_keyboard
    )
    
    await update.message.reply_text(
        "برای بازگشت به منوی اصلی از دکمه زیر استفاده کنید:",
        reply_markup=reply_keyboard
    )
    
    return COPY_NUMBER

async def copy_number_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(
        f"شماره <code>{CONTACT_NUMBER}</code> آماده کپی است!\n\n"
        "حالا می‌توانید:\n"
        "1. در برنامه تلفن خود شماره را پیست کنید\n"
        "2. دکمه تماس را بزنید\n\n"
        "برای بازگشت به منوی اصلی از دکمه زیر استفاده کنید:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK_TO_MAIN]], resize_keyboard=True)
    )
    
    return MAIN_MENU

async def copy_number_handler(update: Update, context: CallbackContext):
    contact_number = "09158708858"
    
    await update.message.reply_text(
        f"شماره <code>{contact_number}</code> آماده کپی است!\n\n"
        "حالا می‌توانید:\n"
        "1. در برنامه تلفن خود شماره را پیست کنید\n"
        "2. دکمه تماس را بزنید\n\n"
        "برای بازگشت به منوی اصلی از دکمه زیر استفاده کنید:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK_TO_MAIN]], resize_keyboard=True)
    )
    
    return MAIN_MENU



# -------------------- بخش وب‌سایت‌ها --------------------
async def websites_menu(update: Update, context: CallbackContext):
    context.user_data['current_menu'] = WEBSITES_MENU  # ذخیره منوی فعلی برای جستجو
    keyboard = [
        [BTN_ECOMMERCE, BTN_CORPORATE],
        [BTN_RESUME, BTN_GALLERY],
        [BTN_WEBSITE_PRICES],
        [BTN_REQUEST_WEBSITE, BTN_SEARCH],  # اضافه کردن دکمه جستجو
        [BTN_BACK_TO_MAIN]
    ]
    # بقیه کد بدون تغییر...
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🌐 *منوی خدمات طراحی وب‌سایت* 🌐\n\n"
        "لطفاً یکی از دسته‌بندی‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return WEBSITES_MENU

async def website_category(update: Update, context: CallbackContext):
    user_input = update.message.text
    
    category_mapping = {
        BTN_ECOMMERCE: "فروشگاهی",
        BTN_CORPORATE: "شرکتی",
        BTN_RESUME: "رزومه",
        BTN_GALLERY: "گالری"
    }
    
    category = category_mapping.get(user_input)
    
    if not category:
        await update.message.reply_text("دسته‌بندی نامعتبر!")
        return WEBSITES_MENU
    
    context.user_data['website_category'] = category
    
    # ارسال پیام در حال دریافت با افکت ناپدید شدن
    loading_msg = await update.message.reply_text("🔍 در حال دریافت لیست نمونه کارها...")
    context.user_data['loading_msg_id'] = loading_msg.message_id
    
    websites = db["websites"].get_all_records()
    category_websites = [w for w in websites if w['Category'] == category]
    
    if not category_websites:
        # ویرایش پیام به جای حذف آن
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=context.user_data['loading_msg_id'],
            text="⏳ نمونه‌کاری در این دسته‌بندی یافت نشد..."
        )
        await asyncio.sleep(1.5)  # تاخیر برای افکت
        
        keyboard = [
            ["منوی وب‌سایت‌ها"],
            ["منوی اصلی"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"در حال حاضر نمونه‌کاری در دسته‌بندی {category} وجود ندارد.",
            reply_markup=reply_markup
        )
        return WEBSITE_CATEGORY
    
    context.user_data['category_websites'] = category_websites
    context.user_data['current_website_index'] = 0
    
    # ویرایش پیام به جای حذف آن
    await context.bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=context.user_data['loading_msg_id'],
        text="✅ نمونه کارها آماده شد!"
    )
    await asyncio.sleep(1)  # تاخیر برای افکت
    
    return await show_website_item(update, context)

async def show_website_item(update: Update, context: CallbackContext):
    websites = context.user_data['category_websites']
    index = context.user_data['current_website_index']
    website = websites[index]
    user_id = update.message.from_user.id
    
    is_favorite = any(
        fav['ItemType'] == 'website' and str(fav['ItemID']) == str(website['ID'])
        for fav in get_user_favorites(user_id)
    )
    
    keyboard = []
    
    fav_button_text = "❌ حذف از علاقه‌مندی‌ها" if is_favorite else "⭐ افزودن به علاقه‌مندی‌ها"
    keyboard.append([fav_button_text])
    
    # اضافه کردن دکمه‌های ناوبری
    nav_buttons = []
    if index > 0:
        nav_buttons.append("◀ قبلی")
    if index < len(websites) - 1:
        nav_buttons.append("بعدی ▶")
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.extend([
        ["ارسال به ادمین", "منوی وب‌سایت‌ها"],
        ["منوی اصلی"]
    ])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    message_text = (
        f"🏷 عنوان: {website['Title']}\n\n"
        f"📝 توضیحات: {website['Description']}\n\n"
        f"🎥 لینک ویدئو: {website['VideoLink'] if website['VideoLink'] else 'ندارد'}"
    )
    
    if website['ImageURL']:
        await update.message.reply_photo(
            photo=website['ImageURL'],
            caption=message_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    return WEBSITE_ITEM


async def website_navigate(update: Update, context: CallbackContext):
    action = update.message.text
    
    if action == "بعدی ▶":
        context.user_data['current_website_index'] += 1
    elif action == "◀ قبلی":
        context.user_data['current_website_index'] -= 1
    
    return await show_website_item(update, context)

async def toggle_website_favorite(update: Update, context: CallbackContext):
    website_id = context.user_data['category_websites'][context.user_data['current_website_index']]['ID']
    user_id = update.message.from_user.id
    
    favorites = get_user_favorites(user_id)
    is_favorite = any(
        fav['ItemType'] == 'website' and str(fav['ItemID']) == str(website_id)
        for fav in favorites
    )
    
    if is_favorite:
        remove_from_favorites(user_id, 'website', website_id)
        await update.message.reply_text("از علاقه‌مندی‌ها حذف شد!")
    else:
        add_to_favorites(user_id, 'website', website_id)
        await update.message.reply_text("به علاقه‌مندی‌ها اضافه شد!")
    
    return await show_website_item(update, context)

async def send_website_to_admin(update: Update, context: CallbackContext):
    try:
        website = context.user_data['category_websites'][context.user_data['current_website_index']]
        user = update.message.from_user
        username = user.username or user.full_name
        
        message = (
            f"🌐 درخواست جدید نمونه کار وبسایت\n\n"
            f"👤 کاربر: {username}\n"
            f"🆔 آیدی: {user.id}\n"
            f"📅 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🏷 عنوان: {website['Title']}\n"
            f"📌 دسته‌بندی: {website['Category']}\n"
            f"📝 توضیحات: {website['Description']}\n"
            f"🔗 لینک ویدئو: {website['VideoLink'] if website['VideoLink'] else 'ندارد'}"
        )
        
        # ارسال پیام و تصویر (اگر وجود داشته باشد)
        image_url = website.get('ImageURL', None)
        if await send_to_admin(context, message, image_url=image_url):
            await update.message.reply_text("✅ نمونه کار با موفقیت به ادمین ارسال شد.")
        else:
            await update.message.reply_text("⚠️ خطا در ارسال به ادمین. لطفاً مجدداً تلاش کنید.")
            
    except Exception as e:
        logger.error(f"خطا در ارسال وبسایت به ادمین: {str(e)}")
        await update.message.reply_text("⚠️ خطایی در ارسال نمونه کار رخ داد. لطفاً مجدداً تلاش کنید.")
    
    return WEBSITE_ITEM


# تابع ارسال ربات تلگرام به ادمین:

async def send_bot_to_admin(update: Update, context: CallbackContext):
    try:
        bot = db["telegram_bots"].get_all_records()[context.user_data['current_bot_index']]
        user = update.message.from_user
        username = user.username or user.full_name
        
        message = (
            f"🤖 درخواست جدید نمونه کار ربات تلگرام\n\n"
            f"👤 کاربر: {username}\n"
            f"🆔 آیدی: {user.id}\n"
            f"📅 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🏷 عنوان: {bot['Title']}\n"
            f"📝 توضیحات: {bot['Description']}\n"
            f"🔗 لینک ویدئو: {bot['VideoLink'] if bot['VideoLink'] else 'ندارد'}"
        )
        
        # ارسال پیام و تصویر (اگر وجود داشته باشد)
        image_url = bot.get('ImageURL', None)
        if await send_to_admin(context, message, image_url=image_url):
            await update.message.reply_text("✅ نمونه کار با موفقیت به ادمین ارسال شد.")
        else:
            await update.message.reply_text("⚠️ خطا در ارسال به ادمین. لطفاً مجدداً تلاش کنید.")
            
    except Exception as e:
        logger.error(f"خطا در ارسال ربات به ادمین: {str(e)}")
        await update.message.reply_text("⚠️ خطایی در ارسال نمونه کار رخ داد. لطفاً مجدداً تلاش کنید.")
    
    return TELEGRAM_BOT_DETAILS

# تابع ارسال نرم‌افزار به ادمین:

async def send_app_to_admin(update: Update, context: CallbackContext):
    try:
        app = db["windows_apps"].get_all_records()[context.user_data['current_app_index']]
        user = update.message.from_user
        username = user.username or user.full_name
        
        message = (
            f"💻 درخواست جدید نمونه کار نرم‌افزار ویندوزی\n\n"
            f"👤 کاربر: {username}\n"
            f"🆔 آیدی: {user.id}\n"
            f"📅 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🏷 عنوان: {app['Title']}\n"
            f"📝 توضیحات: {app['Description']}\n"
            f"🔗 لینک ویدئو: {app['VideoLink'] if app['VideoLink'] else 'ندارد'}"
        )
        
        # ارسال پیام و تصویر (اگر وجود داشته باشد)
        image_url = app.get('ImageURL', None)
        if await send_to_admin(context, message, image_url=image_url):
            await update.message.reply_text("✅ نمونه کار با موفقیت به ادمین ارسال شد.")
        else:
            await update.message.reply_text("⚠️ خطا در ارسال به ادمین. لطفاً مجدداً تلاش کنید.")
            
    except Exception as e:
        logger.error(f"خطا در ارسال نرم‌افزار به ادمین: {str(e)}")
        await update.message.reply_text("⚠️ خطایی در ارسال نمونه کار رخ داد. لطفاً مجدداً تلاش کنید.")
    
    return WINDOWS_APP_DETAILS

async def show_website_prices(update: Update, context: CallbackContext):
    prices = """
🔧 *لیست خدمات طراحی وب‌سایت* 🔧

🖥 **پکیج پایه** (ویترینی):
• طراحی ریسپانسیو و مدرن
• 5 صفحه اصلی (صفحه اصلی، درباره ما، خدمات، نمونه کارها، تماس)
• بهینه‌سازی سئو پایه
• ایجاد فرم دریافت اطلاعات
• پلایگین های اولیه
• امنیت چندلایه
• هاست و دامنه یکساله رایگان
• پلایگین های اولیه
• پشتیبانی 3 ماهه

🛒 **پکیج فروشگاهی**:
• تمامی امکانات پکیج پایه
• سیستم فروش آنلاین پیشرفته
• ایجاد فرم دریافت اطلاعات
• قابلیت اضافه شدن قابلیت خاص
• درگاه پرداخت اینترنتی
• سبد خرید و مدیریت سفارشات
• سیستم تخفیف و کدهای تبلیغاتی
• پلایگین های پیشرفته
• پشتیبانی 6 ماهه

🏢 **پکیج شرکتی**:
• طراحی اختصاصی و منحصر بفرد
• پنل مدیریت پیشرفته
• سیستم بلاگ و اخبار
• فرم‌های تماس پیشرفته
• یکپارچه‌سازی با شبکه‌های اجتماعی
• قابلیت اضافه شدن قابلیت خاص
• پشتیبانی 6 ماهه

💡 *نکات مهم:*
• خدمات به صورت کاملاً سفارشی‌سازی ارائه می‌شود
• امکان اضافه یا کم کردن امکانات وجود دارد
• زمان تحویل پروژه بسته به پیچیدگی متغیر است

📞 برای استعلام دقیق قیمت و دریافت مشاوره رایگان، لطفاً با پشتیبانی تماس بگیرید:
"""
    
    keyboard = [
        [BTN_REQUEST_WEBSITE],
        ["منوی وب‌سایت‌ها"],  # مطمئن شوید متن دقیقاً همین است
        [BTN_BACK_TO_MAIN]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        prices,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return WEBSITES_MENU  # ای

async def request_website(update: Update, context: CallbackContext):
    contact_keyboard = generate_contact_keyboard()
    
    reply_keyboard = ReplyKeyboardMarkup([["انصراف"]], resize_keyboard=True)
    
    message_text = (
        "🌐 *درخواست طراحی وبسایت اختصاصی* 🌐\n\n"
        "📝 لطفاً نیازهای خود را با جزئیات شرح دهید:\n\n"
        "✅ *مثال:*\n"
        "یک وبسایت فروشگاهی با:\n"
        "- طراحی مدرن و ریسپانسیو\n"
        "- درگاه پرداخت آنلاین\n"
        "- پنل مدیریت محتوا\n"
        "- سئو حرفه‌ای\n\n"
        f"📞 پشتیبانی: `{CONTACT_NUMBER}`"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=contact_keyboard,
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(
        "می‌توانید پیام خود را تایپ کنید یا از دکمه‌های بالا برای ارتباط سریع استفاده نمایید:",
        reply_markup=reply_keyboard
    )
    
    return REQUEST_WEBSITE

async def save_website_request(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    try:
        # ذخیره در Google Sheets
        db["support"].append_row([
            user_id,
            username,
            "درخواست وب‌سایت",
            user_text,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Pending"
        ])
        
        # ارسال به ادمین
        admin_message = (
            f"🌐 درخواست جدید وب‌سایت\n\n"
            f"👤 کاربر: {username}\n"
            f"🆔 آیدی: {user_id}\n"
            f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"📝 توضیحات:\n{user_text}"
        )
        
        await send_to_admin(context, admin_message)
        
        keyboard = [[BTN_BACK_TO_MAIN]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "✅ درخواست وب‌سایت شما با موفقیت ثبت شد.\n"
            "همکاران ما به زودی با شما تماس خواهند گرفت.",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"خطا در ثبت درخواست وب‌سایت: {str(e)}")
        await update.message.reply_text("⚠️ خطایی در ثبت درخواست رخ داده است. لطفاً مجدداً تلاش کنید.")
        return REQUEST_WEBSITE

# -------------------- بخش ربات‌های تلگرام --------------------
async def telegram_bots_menu(update: Update, context: CallbackContext):
    context.user_data['current_menu'] = TELEGRAM_BOTS_MENU  # ذخیره منوی فعلی برای جستجو
    keyboard = [
        ["درخواست ربات", "ادامه مطلب"],
        [BTN_SEARCH],  # اضافه کردن دکمه جستجو
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 *ربات‌های هوشمند تلگرامی* - موتور محرک کسب‌وکار دیجیتال شما 🚀\n\n"
        "✨ *با ربات‌های اختصاصی ما، کسب‌وکار خود را متحول کنید!* ✨\n\n"
        "✅ *دسته‌بندی ربات‌های ما:*\n"
        "▫️ *ربات فروشگاهی* - فروش 24 ساعته با پرداخت آنلاین\n"
        "▫️ *ربات پشتیبانی* - پاسخگویی خودکار به مشتریان\n"
        "▫️ *ربات نظرسنجی* - جمع‌آوری داده‌های بازار\n"
        "▫️ *ربات مدیریت محتوا* - انتشار خودکار محتوا\n\n"
        "🛠 *ویژگی‌های کلیدی ربات‌های ما:*\n"
        "• طراحی UI/UX حرفه‌ای\n"
        "• امنیت بالا و پایدار\n"
        "• پنل مدیریت پیشرفته\n"
        "• قابلیت یکپارچه‌سازی با سیستم‌های شما\n\n"
        "📌 *مزایای ربات‌های تلگرامی:*\n"
        "📈 افزایش فروش و تعامل با مشتریان\n"
        "⏱ کاهش هزینه‌های عملیاتی\n"
        "🌍 دسترسی جهانی بدون محدودیت\n\n"
        "👇 برای مشاهده نمونه کارها و جزئیات فنی، گزینه «ادامه مطلب» را انتخاب کنید:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return TELEGRAM_BOTS_MENU

async def show_bot_details(update: Update, context: CallbackContext):
    if 'current_bot_index' not in context.user_data:
        context.user_data['current_bot_index'] = 0
    
    # ارسال پیام در حال دریافت با افکت
    loading_msg = await update.message.reply_text("🔍 در حال دریافت لیست ربات‌ها...")
    context.user_data['loading_msg_id'] = loading_msg.message_id
    
    bot_index = context.user_data['current_bot_index']
    bots = db["telegram_bots"].get_all_records()
    
    if bot_index >= len(bots):
        bot_index = 0
    if bot_index < 0:
        bot_index = len(bots) - 1
    
    context.user_data['current_bot_index'] = bot_index
    bot = bots[bot_index]
    user_id = update.message.from_user.id
    
    is_favorite = any(
        fav['ItemType'] == 'telegram_bot' and str(fav['ItemID']) == str(bot['ID'])
        for fav in get_user_favorites(user_id)
    )
    
    # ویرایش پیام به جای حذف آن
    await context.bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=context.user_data['loading_msg_id'],
        text="✅ اطلاعات ربات آماده شد!"
    )
    await asyncio.sleep(0.8)  # تاخیر کوتاه
    
    keyboard = []
    
    fav_button_text = "❌ حذف از علاقه‌مندی‌ها" if is_favorite else "⭐ افزودن به علاقه‌مندی‌ها"
    keyboard.append([fav_button_text])
    
    # اضافه کردن دکمه‌های ناوبری
    nav_buttons = []
    if bot_index > 0:
        nav_buttons.append("◀ قبلی")
    if bot_index < len(bots) - 1:
        nav_buttons.append("بعدی ▶")
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.extend([
        ["درخواست ربات مشابه"],
        ["منوی ربات‌ها"],
        ["منوی اصلی"]
    ])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    message_text = (
        f"🤖 ربات: {bot['Title']}\n\n"
        f"📝 عملکرد:\n{bot['Description']}\n\n"
        f"🎥 لینک ویدئو: {bot['VideoLink'] if bot['VideoLink'] else 'ندارد'}"
    )
    
    if bot['ImageURL']:
        await update.message.reply_photo(
            photo=bot['ImageURL'],
            caption=message_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    return TELEGRAM_BOT_DETAILS

async def toggle_bot_favorite(update: Update, context: CallbackContext):
    bot_id = db["telegram_bots"].get_all_records()[context.user_data['current_bot_index']]['ID']
    user_id = update.message.from_user.id
    
    favorites = get_user_favorites(user_id)
    is_favorite = any(
        fav['ItemType'] == 'telegram_bot' and str(fav['ItemID']) == str(bot_id)
        for fav in favorites
    )
    
    if is_favorite:
        remove_from_favorites(user_id, 'telegram_bot', bot_id)
        await update.message.reply_text("از علاقه‌مندی‌ها حذف شد!")
    else:
        add_to_favorites(user_id, 'telegram_bot', bot_id)
        await update.message.reply_text("به علاقه‌مندی‌ها اضافه شد!")
    
    return await show_bot_details(update, context)

async def request_bot(update: Update, context: CallbackContext):
    contact_keyboard = generate_contact_keyboard()
    
    reply_keyboard = ReplyKeyboardMarkup([["انصراف"]], resize_keyboard=True)
    
    message_text = (
        "🤖 *درخواست ربات تلگرام اختصاصی* 🤖\n\n"
        "📝 لطفاً نیازهای خود را با جزئیات شرح دهید:\n\n"
        "✅ *مثال:*\n"
        "یک ربات فروشگاهی با قابلیت‌های:\n"
        "- پرداخت آنلاین\n"
        "- مدیریت محصولات\n"
        "- پنل مدیریت\n"
        "- گزارش‌گیری\n\n"
        f"📞 پشتیبانی: `{CONTACT_NUMBER}`"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=contact_keyboard,
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(
        "می‌توانید پیام خود را تایپ کنید یا از دکمه‌های بالا برای ارتباط سریع استفاده نمایید:",
        reply_markup=reply_keyboard
    )
    
    return REQUEST_BOT

async def save_bot_request(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    try:
        # ذخیره در Google Sheets
        db["support"].append_row([
            user_id,
            username,
            "درخواست ربات تلگرام",
            user_text,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Pending"
        ])
        
        # ارسال به ادمین
        admin_message = (
            f"📮 درخواست جدید ربات تلگرام\n\n"
            f"👤 کاربر: {username}\n"
            f"🆔 آیدی: {user_id}\n"
            f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"📝 توضیحات:\n{user_text}"
        )
        
        await send_to_admin(context, admin_message)
        
        keyboard = [[BTN_BACK_TO_MAIN]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "✅ درخواست ربات شما با موفقیت ثبت شد.\n"
            "همکاران ما به زودی با شما تماس خواهند گرفت.",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"خطا در ثبت درخواست ربات: {str(e)}")
        await update.message.reply_text("⚠️ خطایی در ثبت درخواست رخ داده است. لطفاً مجدداً تلاش کنید.")
        return REQUEST_BOT

# -------------------- بخش نرم‌افزارهای ویندوزی --------------------
async def windows_apps_menu(update: Update, context: CallbackContext):
    context.user_data['current_menu'] = WINDOWS_APPS_MENU  # ذخیره منوی فعلی برای جستجو
    keyboard = [
        ["درخواست نرم‌افزار", "نمونه کارها"],
        [BTN_SEARCH],  # اضافه کردن دکمه جستجو
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "💻 *نرم‌افزارهای ویندوزی اختصاصی* 💻\n\n"
        "✨ *قدرت پردازش و کارایی بی‌نظیر برای کسب‌وکار شما* ✨\n\n"
        "✅ *خدمات ما:*\n"
        "▫️ طراحی نرم‌افزارهای مدیریتی و حسابداری\n"
        "▫️ توسعه ابزارهای تخصصی صنعتی\n"
        "▫️ ساخت برنامه‌های چندرسانه‌ای و آموزشی\n"
        "▫️ ایجاد سیستم‌های گزارش‌گیری پیشرفته\n\n"
        "🛠 *ویژگی‌های کلیدی:*\n"
        "• رابط کاربری زیبا و کاربرپسند\n"
        "• امنیت بالا و پایدار\n"
        "• پشتیبانی از چاپ و خروجی‌های مختلف\n"
        "• امکان سفارشی‌سازی کامل\n\n"
        "📌 *مزایای نرم‌افزارهای اختصاصی:*\n"
        "⏱ صرفه‌جویی در زمان و هزینه\n"
        "📈 افزایش بهره‌وری و دقت\n"
        "🔒 امنیت اطلاعات و حریم خصوصی\n\n"
        "👇 برای مشاهده نمونه کارها یا دریافت مشاوره رایگان، یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return WINDOWS_APPS_MENU

async def show_app_details(update: Update, context: CallbackContext):
    if 'current_app_index' not in context.user_data:
        context.user_data['current_app_index'] = 0
    
    # ارسال پیام در حال دریافت و ذخیره message_id
    loading_msg = await update.message.reply_text("🔍 در حال دریافت لیست نمونه کارها...")
    context.user_data['loading_msg_id'] = loading_msg.message_id
    
    app_index = context.user_data['current_app_index']
    apps = db["windows_apps"].get_all_records()
    
    if app_index >= len(apps):
        app_index = 0
    if app_index < 0:
        app_index = len(apps) - 1
    
    context.user_data['current_app_index'] = app_index
    app = apps[app_index]
    user_id = update.message.from_user.id
    
    is_favorite = any(
        fav['ItemType'] == 'windows_app' and str(fav['ItemID']) == str(app['ID'])
        for fav in get_user_favorites(user_id)
    )
    
    # حذف پیام در حال دریافت قبل از نمایش نمونه کار
    await context.bot.delete_message(
        chat_id=update.message.chat_id,
        message_id=context.user_data['loading_msg_id']
    )
    
    keyboard = []
    
    fav_button_text = "❌ حذف از علاقه‌مندی‌ها" if is_favorite else "⭐ افزودن به علاقه‌مندی‌ها"
    keyboard.append([fav_button_text])
    
    # اضافه کردن دکمه‌های ناوبری
    nav_buttons = []
    if app_index > 0:
        nav_buttons.append("◀ قبلی")
    if app_index < len(apps) - 1:
        nav_buttons.append("بعدی ▶")
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.extend([
        ["درخواست نرم‌افزار مشابه"],
        ["منوی نرم‌افزارها"],
        ["منوی اصلی"]
    ])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    message_text = (
        f"💻 نرم‌افزار: {app['Title']}\n\n"
        f"📝 توضیحات:\n{app['Description']}\n\n"
        f"🎥 لینک ویدئو: {app['VideoLink'] if app['VideoLink'] else 'ندارد'}"
    )
    
    if app['ImageURL']:
        await update.message.reply_photo(
            photo=app['ImageURL'],
            caption=message_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    return WINDOWS_APP_DETAILS

async def toggle_app_favorite(update: Update, context: CallbackContext):
    app_id = db["windows_apps"].get_all_records()[context.user_data['current_app_index']]['ID']
    user_id = update.message.from_user.id
    
    favorites = get_user_favorites(user_id)
    is_favorite = any(
        fav['ItemType'] == 'windows_app' and str(fav['ItemID']) == str(app_id)
        for fav in favorites
    )
    
    if is_favorite:
        remove_from_favorites(user_id, 'windows_app', app_id)
        await update.message.reply_text("از علاقه‌مندی‌ها حذف شد!")
    else:
        add_to_favorites(user_id, 'windows_app', app_id)
        await update.message.reply_text("به علاقه‌مندی‌ها اضافه شد!")
    
    return await show_app_details(update, context)

async def request_app(update: Update, context: CallbackContext):
    contact_keyboard = generate_contact_keyboard()
    
    reply_keyboard = ReplyKeyboardMarkup([["انصراف"]], resize_keyboard=True)
    
    message_text = (
        "💻 *درخواست نرم‌افزار ویندوزی اختصاصی* 💻\n\n"
        "📝 لطفاً نیازهای خود را با جزئیات شرح دهید:\n\n"
        "✅ *مثال:*\n"
        "یک نرم‌افزار حسابداری با قابلیت‌های:\n"
        "- صدور فاکتور و پیش‌فاکتور\n"
        "- گزارش‌گیری مالی و آماری\n"
        "- پشتیبان‌گیری خودکار\n"
        "- مدیریت انبار و موجودی\n\n"
        f"📞 پشتیبانی: `{CONTACT_NUMBER}`"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=contact_keyboard,
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(
        "می‌توانید پیام خود را تایپ کنید یا از دکمه‌های بالا برای ارتباط سریع استفاده نمایید:",
        reply_markup=reply_keyboard
    )
    
    return REQUEST_APP
def create_contact_section(contact_number):
    whatsapp_url = f"https://wa.me/{contact_number}"
    
    buttons = [
        InlineKeyboardButton("💬 واتساپ", url=whatsapp_url),
        InlineKeyboardButton("📋 کپی شماره", callback_data=f"copy_number_{contact_number}")
    ]
    
    keyboard = InlineKeyboardMarkup([buttons])
    
    text = (
        f"📞 *پشتیبانی:* `{contact_number}`\n"
        f"▫️ [ارتباط از طریق واتساپ]({whatsapp_url})\n"
        "▫️ یا شماره را کپی کنید"
    )
    
    return text, keyboard    
#جستجو در آیتم‌ها

async def search_items(update: Update, context: CallbackContext):
    keyboard = [
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🔍 لطفاً عبارت جستجو را وارد کنید:\n\n"
        "مثال:\n"
        "- آرایشی\n"
        "- فروشگاهی\n"
        "- مدیریتی\n"
        "- آموزشی",
        reply_markup=reply_markup
    )
    return SEARCH_ITEMS

async def handle_search(update: Update, context: CallbackContext):
    user_input = update.message.text
    
    # اگر کاربر دکمه منوی اصلی را زد
    if user_input == BTN_BACK_TO_MAIN:
        return await start(update, context)
    
    search_query = user_input.lower()
    current_menu = context.user_data.get('current_menu')

    # تعیین نوع آیتم‌ها بر اساس منوی فعلی
    if current_menu == WEBSITES_MENU:
        sheet_name = 'websites'
        item_type = 'website'
    elif current_menu == TELEGRAM_BOTS_MENU:
        sheet_name = 'telegram_bots'
        item_type = 'telegram_bot'
    elif current_menu == WINDOWS_APPS_MENU:
        sheet_name = 'windows_apps'
        item_type = 'windows_app'
    else:
        await update.message.reply_text("خطا در جستجو! لطفاً از منوی اصلی دوباره شروع کنید.")
        return MAIN_MENU

    # جستجو در گوگل شیت
    all_items = db[sheet_name].get_all_records()
    found_items = [
        item for item in all_items
        if search_query in item.get('Tags', '').lower() or 
           search_query in item.get('Title', '').lower() or
           search_query in item.get('Description', '').lower()
    ]

    if not found_items:
        keyboard = [
            ["جستجوی مجدد"],
            ["منوی اصلی"]
        ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"نتیجه‌ای برای '{search_query}' یافت نشد.\n\n"
            "می‌توانید:\n"
            "- با واژه دیگری جستجو کنید\n"
            "- به منوی اصلی بازگردید",
            reply_markup=reply_markup
        )
        return SEARCH_ITEMS  # باقی ماندن در حالت جستجو برای تلاش مجدد

    context.user_data['search_results'] = found_items
    context.user_data['current_item_index'] = 0
    context.user_data['search_query'] = search_query

    return await show_search_result(update, context)

async def show_search_result(update: Update, context: CallbackContext):
    found_items = context.user_data['search_results']
    index = context.user_data['current_item_index']
    item = found_items[index]
    search_query = context.user_data['search_query']

    keyboard = []
    
    # دکمه‌های ناوبری
    nav_buttons = []
    if index > 0:
        nav_buttons.append("◀ قبلی")
    if index < len(found_items) - 1:
        nav_buttons.append("بعدی ▶")
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append(["جستجوی جدید"])
    keyboard.append(["منوی اصلی"])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    message_text = (
        f"🔍 نتایج برای '{search_query}'\n\n"
        f"🏷 عنوان: {item['Title']}\n\n"
        f"📝 توضیحات: {item['Description']}\n\n"
        f"🏷 برچسب‌ها: {item.get('Tags', 'بدون برچسب')}\n\n"
        f"🔄 نتیجه {index + 1} از {len(found_items)}"
    )

    if item.get('ImageURL'):
        await update.message.reply_photo(
            photo=item['ImageURL'],
            caption=message_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )

    return SEARCH_ITEMS

async def navigate_search_results(update: Update, context: CallbackContext):
    action = update.message.text
    
    if action == "بعدی ▶":
        context.user_data['current_item_index'] += 1
    elif action == "◀ قبلی":
        context.user_data['current_item_index'] -= 1
    
    return await show_search_result(update, context)

async def show_search_result(update: Update, context: CallbackContext):
    found_items = context.user_data['search_results']
    index = context.user_data['current_item_index']
    item = found_items[index]
    search_query = context.user_data['search_query']

    keyboard = []
    
    # دکمه‌های ناوبری
    nav_buttons = []
    if index > 0:
        nav_buttons.append("◀ قبلی")
    if index < len(found_items) - 1:
        nav_buttons.append("بعدی ▶")
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append(["جستجوی جدید"])
    keyboard.append(["منوی اصلی"])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    message_text = (
        f"🔍 نتایج برای '{search_query}'\n\n"
        f"🏷 عنوان: {item['Title']}\n\n"
        f"📝 توضیحات: {item['Description']}\n\n"
        f"🏷 برچسب‌ها: {item.get('Tags', 'بدون برچسب')}\n\n"
        f"🔄 نتیجه {index + 1} از {len(found_items)}"
    )

    if item.get('ImageURL'):
        await update.message.reply_photo(
            photo=item['ImageURL'],
            caption=message_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )

    return SEARCH_ITEMS

async def navigate_search_results(update: Update, context: CallbackContext):
    action = update.message.text
    
    if action == "بعدی ▶":
        context.user_data['current_item_index'] += 1
    elif action == "◀ قبلی":
        context.user_data['current_item_index'] -= 1
    
    return await show_search_result(update, context)



# -------------------- توابع کمکی تماس --------------------
def generate_contact_keyboard(contact_number="09158708858"):
    whatsapp_url = f"https://wa.me/{contact_number}"
    
    buttons = [
        InlineKeyboardButton("💬 گفتگو در واتساپ", url=whatsapp_url),
        InlineKeyboardButton("📋 کپی شماره", callback_data=f"copy_number_{contact_number}")
    ]
    
    return InlineKeyboardMarkup([buttons])

CONTACT_NUMBER = "09158708858"  # این را در بخش تعریف متغیرهای全局 اضافه کنید



async def handle_copy_app_number(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    contact_number = "09158708858"
    
    await query.edit_message_text(
        f"شماره <code>{contact_number}</code> کپی شد!\n\n"
        "حالا می‌توانید:\n"
        "1. در برنامه مورد نظر پیست کنید\n"
        "2. با ما تماس بگیرید\n\n"
        "برای ادامه، پیام خود را ارسال کنید:",
        parse_mode='HTML'
    )
async def save_app_request(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    try:
        # ذخیره در Google Sheets
        db["support"].append_row([
            user_id,
            username,
            "درخواست نرم‌افزار ویندوزی",
            user_text,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Pending"
        ])
        
        # ارسال به ادمین
        admin_message = (
            f"💻 درخواست جدید نرم‌افزار ویندوزی\n\n"
            f"👤 کاربر: {username}\n"
            f"🆔 آیدی: {user_id}\n"
            f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"📝 توضیحات:\n{user_text}"
        )
        
        await send_to_admin(context, admin_message)
        
        keyboard = [[BTN_BACK_TO_MAIN]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "✅ درخواست نرم‌افزار شما با موفقیت ثبت شد.\n"
            "همکاران ما به زودی با شما تماس خواهند گرفت.",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"خطا در ثبت درخواست نرم‌افزار: {str(e)}")
        await update.message.reply_text("⚠️ خطایی در ثبت درخواست رخ داده است. لطفاً مجدداً تلاش کنید.")
        return REQUEST_APP

# -------------------- بخش پشتیبانی --------------------
async def support_menu(update: Update, context: CallbackContext):
    contact_keyboard = generate_contact_keyboard()
    
    keyboard = [
        ["درخواست پشتیبانی/مشاوره"],
        [BTN_BACK_TO_MAIN]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🔧 *خدمات حرفه‌ای پشتیبانی و بهینه‌سازی* 🔧\n\n"
        "ما با تیم متخصص خود آماده ارائه خدمات:\n\n"
        "🛠 *پشتیبانی فنی:*\n"
        "• رفع باگ‌ها و مشکلات فوری\n"
        "• بهینه‌سازی سرعت بارگذاری\n"
        "• افزایش امنیت و جلوگیری از نفوذ\n\n"
        "⚡ *بهینه‌سازی حرفه‌ای:*\n"
        "• بهبود سئو فنی\n"
        "• تحلیل و رفع مشکلات عملکردی\n\n"
        f"📞 *پشتیبانی فوری:* `{CONTACT_NUMBER}`",
        reply_markup=contact_keyboard,
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(
        "برای ثبت درخواست پشتیبانی یا دریافت مشاوره تخصصی، گزینه زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return SUPPORT_MENU


async def request_support(update: Update, context: CallbackContext):
    contact_keyboard = generate_contact_keyboard()
    
    reply_keyboard = ReplyKeyboardMarkup([["انصراف"]], resize_keyboard=True)
    
    message_text = (
        "📢 *ثبت درخواست پشتیبانی/مشاوره* 📢\n\n"
        "لطفاً به دقت توضیح دهید:\n"
        "• نوع مشکل یا درخواست شما\n"
        "• آدرس سایت (اگر مربوط به وبسایت است)\n"
        "• تصویری از خطا (در صورت وجود)\n\n"
        "✅ *مثال:*\n"
        "سایت وردپرسی من پس از آپدیت دچار مشکل شده است:\n"
        "- آدرس سایت: example.com\n"
        "- خطای 500 دریافت می‌کنم\n"
        "- مشکل پس از آپدیت پلاگین رخ داده\n\n"
        f"📞 *پشتیبانی فوری:* `{CONTACT_NUMBER}`\n"
        "می‌توانید از دکمه‌های زیر برای ارتباط سریع استفاده کنید:"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=contact_keyboard,
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(
        "پیام خود را وارد کنید یا در صورت نیاز از دکمه انصراف استفاده نمایید:",
        reply_markup=reply_keyboard
    )
    
    return REQUEST_SUPPORT

async def save_support_request(update: Update, context: CallbackContext):
    # اگر کاربر انصراف داد
    if update.message.text == "انصراف":
        return await support_menu(update, context)
    
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    try:
        # ذخیره در Google Sheets
        db["support"].append_row([
            user_id,
            username,
            "درخواست پشتیبانی",
            user_text,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Pending"
        ])
        
        # ارسال به ادمین
        admin_message = (
            f"🛠 درخواست جدید پشتیبانی\n\n"
            f"👤 کاربر: {username}\n"
            f"🆔 آیدی: {user_id}\n"
            f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"📝 توضیحات:\n{user_text}"
        )
        
        await send_to_admin(context, admin_message)
        
        keyboard = [[BTN_BACK_TO_MAIN]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "✅ درخواست پشتیبانی شما با موفقیت ثبت شد.\n"
            "همکاران ما به زودی با شما تماس خواهند گرفت.",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"خطا در ثبت درخواست پشتیبانی: {str(e)}")
        await update.message.reply_text(
            "⚠️ خطایی در ثبت درخواست رخ داده است. لطفاً مجدداً تلاش کنید.",
            reply_markup=ReplyKeyboardMarkup([["انصراف"]], resize_keyboard=True)
        )
        return REQUEST_SUPPORT

# -------------------- بخش مشاوره --------------------
async def consultation_menu(update: Update, context: CallbackContext):
    contact_keyboard = generate_contact_keyboard()
    
    # فقط دکمه منوی اصلی را نمایش دهید
    reply_keyboard = ReplyKeyboardMarkup([[BTN_BACK_TO_MAIN]], resize_keyboard=True)
    
    message_text = (
        "📞 *مشاوره تخصصی رایگان* 📞\n\n"
        "✅ زمینه‌های مشاوره:\n"
        "- طراحی وب‌سایت\n"
        "- توسعه ربات تلگرام\n"
        "- نرم‌افزارهای ویندوزی\n"
        "- بهینه‌سازی و سئو\n\n"
        "لطفاً سوال یا درخواست مشاوره خود را مطرح کنید:"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=reply_keyboard
    )
    
    return CONSULTATION

async def handle_copy_number(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    contact_number = query.data.replace("copy_number_", "")
    
    await query.edit_message_text(
        f"شماره <code>{contact_number}</code> کپی شد!\n\n"
        "حالا می‌توانید:\n"
        "1. در برنامه مورد نظر پیست کنید\n"
        "2. با ما تماس بگیرید",
        parse_mode='HTML'
    )
async def handle_contact(update: Update, context: CallbackContext):
    contact = update.message.contact
    phone_number = contact.phone_number
    
    # ذخیره شماره تماس کاربر
    context.user_data['user_phone'] = phone_number
    
    await update.message.reply_text(
        f"شماره تماس شما ({phone_number}) دریافت شد.\n\n"
        "لطفاً توضیحات درخواست مشاوره خود را وارد کنید:"
    )
    
    return CONSULTATION
async def save_consultation(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    # ذخیره در Google Sheets
    db["support"].append_row([
        user_id,
        username,
        "درخواست مشاوره",
        user_text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Pending"
    ])
    
    # ارسال به ادمین
    admin_message = (
        f"درخواست جدید مشاوره:\n"
        f"کاربر: {username} (آیدی: {user_id})\n\n"
        f"توضیحات:\n{user_text}"
    )
    try:
        await context.bot.send_message(
            chat_id=1810708143,
            text=admin_message
        )
    except Exception as e:
        logger.error(f"خطا در ارسال پیام به ادمین: {str(e)}")
    
    keyboard = [[BTN_BACK_TO_MAIN]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ درخواست شما با موفقیت ثبت شد.\n"
        "پس از بررسی با شما تماس گرفته خواهد شد.",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

async def fallback_handler(update: Update, context: CallbackContext):
    keyboard = [[BTN_BACK_TO_MAIN]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "⚠️ لطفاً از دکمه‌های منو استفاده کنید:",
        reply_markup=reply_markup
    )
    return MAIN_MENU
# ارسال به ادمین

async def send_to_admin(context: CallbackContext, message: str, chat_id: int = 1810708143, image_url: str = None):
    try:
        if image_url:  # اگر URL تصویر وجود داشته باشد
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=image_url,
                caption=message
            )
        else:  # اگر تصویری وجود نداشته باشد، فقط متن ارسال شود
            await context.bot.send_message(
                chat_id=chat_id,
                text=message
            )
        logger.info(f"پیام با موفقیت به ادمین ارسال شد: {message[:50]}...")
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال پیام به ادمین: {str(e)}")
        return False

async def save_and_notify(context: CallbackContext, sheet_name: str, data: list, message: str):
    # ذخیره در Google Sheets
    db[sheet_name].append_row(data)
    
    # ارسال به ادمین
    await context.bot.send_message(
        chat_id=1810708143,
        text=message
    )
# -------------------- بخش درباره من --------------------
async def about_menu(update: Update, context: CallbackContext):
    keyboard = [
        ["درخواست مشاوره"],
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    about_text = (
        "👋 من نوید راد هستم، طراح و توسعه‌دهنده نرم‌افزار\n\n"
        "✅ 12 سال سابقه فعالیت در حوزه فناوری اطلاعات\n"
        "✅ 6 سال تجربه حرفه‌ای در توسعه وب و نرم‌افزار\n"
        "✅ طراحی بیش از 150 پروژه موفق\n\n"
        "🛠 تخصص‌های اصلی:\n"
        "- طراحی وب‌سایت‌های اختصاصی\n"
        "- توسعه ربات‌های تلگرام پیشرفته\n"
        "- ساخت نرم‌افزارهای ویندوزی\n"
        "- پشتیبانی و بهینه‌سازی سیستم‌های موجود\n\n"
        "📌 برای شروع همکاری یا دریافت مشاوره می‌توانید از دکمه زیر استفاده کنید:"
    )
    
    await update.message.reply_text(
        about_text,
        reply_markup=reply_markup
    )
    
    return ABOUT_MENU

# -------------------- بخش لیست علاقه‌مندی‌ها --------------------
async def favorites_menu(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    # ارسال پیام در حال دریافت و ذخیره message_id
    loading_msg = await update.message.reply_text("🔍 در حال دریافت لیست علاقه‌مندی‌ها...")
    context.user_data['loading_msg_id'] = loading_msg.message_id
    
    favorites = get_user_favorites(user_id)
    
    if not favorites:
        # حذف پیام در حال دریافت
        await context.bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=context.user_data['loading_msg_id']
        )
        
        keyboard = [
            ["منوی اصلی"]
        ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🌟 لیست علاقه‌مندی‌های شما خالی است.\n\n"
            "می‌توانید با استفاده از دکمه ⭐ در بخش‌های مختلف، "
            "آیتم‌های مورد علاقه خود را ذخیره کنید.",
            reply_markup=reply_markup
        )
        return FAVORITES_MENU
    
    context.user_data['user_favorites'] = favorites
    context.user_data['current_favorite_index'] = 0
    
    # حذف پیام در حال دریافت
    await context.bot.delete_message(
        chat_id=update.message.chat_id,
        message_id=context.user_data['loading_msg_id']
    )
    
    return await show_favorite_item(update, context)

async def show_favorite_item(update: Update, context: CallbackContext):
    favorites = context.user_data['user_favorites']
    index = context.user_data['current_favorite_index']
    favorite = favorites[index]
    
    # ارسال پیام در حال دریافت و ذخیره message_id
    loading_msg = await update.message.reply_text("🔍 در حال دریافت اطلاعات آیتم...")
    context.user_data['loading_msg_id'] = loading_msg.message_id
    
    # دریافت اطلاعات آیتم از دیتابیس مربوطه
    item_type = favorite['ItemType']
    item_id = favorite['ItemID']
    
    if item_type == 'website':
        sheet = db["websites"]
        item = next((w for w in sheet.get_all_records() if w['ID'] == item_id), None)
        item_type_fa = "وب‌سایت"
        item_title = item['Title'] if item else "وب‌سایت (حذف شده)"
        description = item['Description'] if item else "این آیتم دیگر موجود نیست"
        image_url = item.get('ImageURL', None) if item else None
    elif item_type == 'telegram_bot':
        sheet = db["telegram_bots"]
        item = next((b for b in sheet.get_all_records() if b['ID'] == item_id), None)
        item_type_fa = "ربات تلگرام"
        item_title = item['Title'] if item else "ربات تلگرام (حذف شده)"
        description = item['Description'] if item else "این آیتم دیگر موجود نیست"
        image_url = item.get('ImageURL', None) if item else None
    elif item_type == 'windows_app':
        sheet = db["windows_apps"]
        item = next((a for a in sheet.get_all_records() if a['ID'] == item_id), None)
        item_type_fa = "نرم‌افزار ویندوزی"
        item_title = item['Title'] if item else "نرم‌افزار (حذف شده)"
        description = item['Description'] if item else "این آیتم دیگر موجود نیست"
        image_url = item.get('ImageURL', None) if item else None
    else:
        item_type_fa = "آیتم ناشناخته"
        item_title = "آیتم ناشناخته"
        description = "نوع این آیتم شناسایی نشد"
        image_url = None
    
    # حذف پیام در حال دریافت قبل از نمایش آیتم
    await context.bot.delete_message(
        chat_id=update.message.chat_id,
        message_id=context.user_data['loading_msg_id']
    )
    
    # آماده‌سازی کیبورد
    keyboard = []
    
    # دکمه‌های ناوبری
    nav_buttons = []
    if index > 0:
        nav_buttons.append("◀ قبلی")
    if index < len(favorites) - 1:
        nav_buttons.append("بعدی ▶")
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.extend([
        ["🗑 حذف از علاقه‌مندی‌ها"],
        ["📩 ارسال به ادمین"],
        ["منوی اصلی"]
    ])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # آماده‌سازی متن پیام
    message_text = (
        f"🔖 آیتم {index + 1} از {len(favorites)}\n\n"
        f"📌 نوع: {item_type_fa}\n"
        f"🏷 عنوان: {item_title}\n\n"
        f"📝 توضیحات:\n{description}\n"
        f"🔗 لینک ویدئو: {item.get('VideoLink', 'ندارد') if item else 'ندارد'}"
    )
    
    # ارسال پیام با تصویر یا بدون تصویر
    if image_url:
        await update.message.reply_photo(
            photo=image_url,
            caption=message_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    return FAVORITES_MENU

async def navigate_favorites(update: Update, context: CallbackContext):
    action = update.message.text
    
    if action == "بعدی ▶":
        context.user_data['current_favorite_index'] += 1
    elif action == "◀ قبلی":
        context.user_data['current_favorite_index'] -= 1
    
    return await show_favorite_item(update, context)

async def remove_favorite(update: Update, context: CallbackContext):
    favorite = context.user_data['user_favorites'][context.user_data['current_favorite_index']]
    item_type = favorite['ItemType']
    item_id = int(favorite['ItemID'])
    user_id = update.message.from_user.id
    
    if remove_from_favorites(user_id, item_type, item_id):
        await update.message.reply_text("آیتم از علاقه‌مندی‌ها حذف شد!")
    else:
        await update.message.reply_text("خطا در حذف آیتم!")
    
    # به روزرسانی لیست علاقه‌مندی‌ها
    favorites = get_user_favorites(user_id)
    context.user_data['user_favorites'] = favorites
    
    if not favorites:
        return await favorites_menu(update, context)
    
    # تنظیم مجدد index اگر از محدوده خارج شده باشد
    if context.user_data['current_favorite_index'] >= len(favorites):
        context.user_data['current_favorite_index'] = len(favorites) - 1
    
    return await show_favorite_item(update, context)

async def send_favorite_to_admin(update: Update, context: CallbackContext):
    favorite = context.user_data['user_favorites'][context.user_data['current_favorite_index']]
    item_type = favorite['ItemType']
    item_id = int(favorite['ItemID'])
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    # دریافت اطلاعات آیتم
    if item_type == 'website':
        sheet = db["websites"]
        item = next((w for w in sheet.get_all_records() if w['ID'] == item_id), None)
        item_type_fa = "وب‌سایت"
    elif item_type == 'telegram_bot':
        sheet = db["telegram_bots"]
        item = next((b for b in sheet.get_all_records() if b['ID'] == item_id), None)
        item_type_fa = "ربات تلگرام"
    elif item_type == 'windows_app':
        sheet = db["windows_apps"]
        item = next((a for a in sheet.get_all_records() if a['ID'] == item_id), None)
        item_type_fa = "نرم‌افزار ویندوزی"
    else:
        item = None
        item_type_fa = "آیتم ناشناخته"
    
    if item:
        message = (
            f"کاربر {username} (آیدی: {user_id}) آیتم زیر را از علاقه‌مندی‌های خود برای شما ارسال کرده:\n\n"
            f"نوع: {item_type_fa}\n"
            f"عنوان: {item['Title']}\n"
            f"توضیحات: {item['Description']}\n"
            f"🔗 لینک ویدئو: {item['VideoLink'] if item['VideoLink'] else 'ندارد'}"
        )
        image_url = item.get('ImageURL', None)
        if await send_to_admin(context, message, image_url=image_url):
            await update.message.reply_text("✅ آیتم با موفقیت به ادمین ارسال شد!")
        else:
            await update.message.reply_text("⚠️ خطا در ارسال به ادمین. لطفاً مجدداً تلاش کنید.")
    else:
        await update.message.reply_text("⚠️ خطا در یافتن آیتم!")
    
    return FAVORITES_MENU

async def navigate_search_results(update: Update, context: CallbackContext):
    """هدایت بین نتایج جستجو"""
    action = update.message.text
    
    # به روزرسانی index بر اساس دکمه فشرده شده
    if action == "بعدی ▶":
        context.user_data['current_item_index'] += 1
    elif action == "◀ قبلی":
        context.user_data['current_item_index'] -= 1
    
    # نمایش نتیجه جدید
    return await show_search_result(update, context)

async def services_menu(update: Update, context: CallbackContext):
    # دریافت خدمات از دیتابیس
    services = db["services"].get_all_records()
    
    # ایجاد کیبورد
    keyboard = [
        ["درخواست مشاوره"],
        [BTN_BACK_TO_MAIN]  
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # ایجاد متن خدمات با قابلیت Markdown
    services_text = (
        "🌟 *خدمات دیجیتال مارکتینگ و توسعه حرفه‌ای* 🌟\n\n"
        "🔹 *طراحی حرفه‌ای لوگو و هویت بصری:*\n"
        "• طراحی لوگو منحصر بفرد\n"
        "• راهنمای رنگ و فونت (Style Guide)\n"
        "• طراحی کارت ویزیت و سربرگ\n\n"
        "📈 *خدمات اینستاگرام و شبکه‌های اجتماعی:*\n"
        "• افزایش تعامل و رشد فالوور\n\n"
        "🖥 *طراحی صفحات ویژه (لندینگ پیج):*\n"
        "• طراحی جذاب و تبدیل محور\n"
        "• بهینه‌سازی برای تبدیل بالاتر\n\n"
        "📊 *سیستم‌های گزارش‌گیری و تحلیل:*\n"
        "• داشبوردهای مدیریتی\n"
        "• گزارش‌های سفارشی\n"
        "• آنالیز داده‌های کسب‌وکار\n\n"
        "🎨 *سایر خدمات تخصصی:*\n"
        "• طراحی رابط کاربری (UI/UX)\n"
        "• تولید محتوای متنی و تصویری\n"
        "• بهینه‌سازی سئو\n\n"
        "💡 *چرا خدمات ما متفاوت است؟*\n"
        "✅ تیم متخصص با 10+ سال تجربه\n"
        "✅ پشتیبانی 24/7\n"
        "✅ قیمت‌های رقابتی\n"
        "✅ تضمین کیفیت\n\n"
        f"📞 برای مشاوره رایگان همین حالا با ما تماس بگیرید: `{CONTACT_NUMBER}`"
    )
    
    # ارسال پیام نهایی
    await update.message.reply_text(
        services_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SERVICES_MENU

# -------------------- راه‌اندازی ربات --------------------
def main():
    try:
        application = ApplicationBuilder().token("8108226042:AAGUY9msPTe_YTBQ6omHGmeNQbNp1ULo1bU").build()
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            
            states={
                MAIN_MENU: [
                    MessageHandler(filters.Text(BTN_WEBSITES), websites_menu),
                    MessageHandler(filters.Text(BTN_TELEGRAM_BOTS), telegram_bots_menu),
                    MessageHandler(filters.Text(BTN_WINDOWS_APPS), windows_apps_menu),
                    MessageHandler(filters.Text(BTN_SUPPORT), support_menu),
                    MessageHandler(filters.Text(BTN_CONSULTATION), consultation_menu),
                    MessageHandler(filters.Text(BTN_ABOUT), about_menu),
                    MessageHandler(filters.Text(BTN_FAVORITES), favorites_menu),
                    MessageHandler(filters.Text(BTN_SERVICES), services_menu),
                    MessageHandler(filters.Text(BTN_CONTACT), handle_contact_request),
                    MessageHandler(filters.Text(BTN_BACK_TO_MAIN), start), 
                ],
                SEARCH_ITEMS: [
                    MessageHandler(filters.Text(BTN_BACK_TO_MAIN) | filters.Text("منوی اصلی"), start),
                    MessageHandler(filters.Text("جستجوی جدید") | filters.Text("جستجوی مجدد"), search_items),
                    MessageHandler(filters.Text("◀ قبلی") | filters.Text("بعدی ▶"), navigate_search_results),
                    MessageHandler(filters.TEXT & ~filters.Text([BTN_BACK_TO_MAIN, "◀ قبلی", "بعدی ▶", "جستجوی جدید", "جستجوی مجدد", "منوی اصلی"]), handle_search),
                ],
    
                COPY_NUMBER: [
                    MessageHandler(filters.Text("📱 کپی شماره پشتیبانی"), copy_number_handler),
                    MessageHandler(filters.Text(BTN_BACK_TO_MAIN), start),
                    MessageHandler(filters.Text(BTN_CONTACT), handle_contact_request),  # این خط مهم است

                ],

                WEBSITES_MENU: [
                    MessageHandler(filters.Text(BTN_ECOMMERCE) | 
                                filters.Text(BTN_CORPORATE) | 
                                filters.Text(BTN_RESUME) | 
                                filters.Text(BTN_GALLERY), website_category),
                    MessageHandler(filters.Text(BTN_SEARCH), search_items),
                    MessageHandler(filters.Text(BTN_WEBSITE_PRICES), show_website_prices),
                    MessageHandler(filters.Text(BTN_REQUEST_WEBSITE), request_website),
                    MessageHandler(filters.Text("منوی وب‌سایت‌ها"), websites_menu),  # این خط جدید
                    MessageHandler(filters.Text(BTN_BACK_TO_MAIN), start),
                    MessageHandler(filters.Text(BTN_CONTACT), handle_contact_request),  
                ],
                WEBSITE_CATEGORY: [
                    MessageHandler(filters.Text("⭐ افزودن به علاقه‌مندی‌ها") | 
                                 filters.Text("❌ حذف از علاقه‌مندی‌ها"), toggle_website_favorite),
                    MessageHandler(filters.Text("◀ قبلی") | filters.Text("بعدی ▶"), website_navigate),
                    MessageHandler(filters.Text("ارسال به ادمین"), send_website_to_admin),
                    MessageHandler(filters.Text("منوی وب‌سایت‌ها"), websites_menu),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                WEBSITE_ITEM: [
                    MessageHandler(filters.Text("⭐ افزودن به علاقه‌مندی‌ها") | 
                    filters.Text("❌ حذف از علاقه‌مندی‌ها"), toggle_website_favorite),
                    MessageHandler(filters.Text("◀ قبلی") | filters.Text("بعدی ▶"), website_navigate),
                    MessageHandler(filters.Text("ارسال به ادمین"), send_website_to_admin),
                    MessageHandler(filters.Text("منوی وب‌سایت‌ها"), websites_menu),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],

                REQUEST_WEBSITE: [
                    MessageHandler(filters.TEXT & ~filters.Text("انصراف"), save_website_request),
                    MessageHandler(filters.Text("انصراف"), websites_menu),
                ],
                TELEGRAM_BOTS_MENU: [
                    MessageHandler(filters.Text("ادامه مطلب"), show_bot_details),
                    MessageHandler(filters.Text("درخواست ربات"), request_bot),
                    MessageHandler(filters.Text(BTN_SEARCH), search_items),  # اضافه کردن handler جستجو
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                TELEGRAM_BOT_DETAILS: [
                    MessageHandler(filters.Text("⭐ افزودن به علاقه‌مندی‌ها") | 
                    filters.Text("❌ حذف از علاقه‌مندی‌ها"), toggle_bot_favorite),
                    MessageHandler(filters.Text("◀ قبلی") | filters.Text("بعدی ▶"), show_bot_details),
                    MessageHandler(filters.Text("درخواست ربات مشابه"), request_bot),
                    MessageHandler(filters.Text("منوی ربات‌ها"), telegram_bots_menu),
                    MessageHandler(filters.Text("ارسال به ادمین"), send_bot_to_admin),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                REQUEST_BOT: [
                    MessageHandler(filters.TEXT & ~filters.Text("انصراف"), save_bot_request),
                    MessageHandler(filters.Text("انصراف"), telegram_bots_menu),
                ],
                WINDOWS_APPS_MENU: [
                    MessageHandler(filters.Text("نمونه کارها"), show_app_details),
                    MessageHandler(filters.Text("درخواست نرم‌افزار"), request_app),
                    MessageHandler(filters.Text(BTN_SEARCH), search_items),  # اضافه کردن handler جستجو
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                WINDOWS_APP_DETAILS: [
                    MessageHandler(filters.Text("⭐ افزودن به علاقه‌مندی‌ها") | 
                    filters.Text("❌ حذف از علاقه‌مندی‌ها"), toggle_app_favorite),
                    MessageHandler(filters.Text("◀ قبلی") | filters.Text("بعدی ▶"), show_app_details),
                    MessageHandler(filters.Text("درخواست نرم‌افزار مشابه"), request_app),
                    MessageHandler(filters.Text("منوی نرم‌افزارها"), windows_apps_menu),
                    MessageHandler(filters.Text("ارسال به ادمین"), send_app_to_admin),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                REQUEST_APP: [
                    MessageHandler(filters.TEXT & ~filters.Text("انصراف"), save_app_request),
                    MessageHandler(filters.Text("انصراف"), windows_apps_menu),
                ],
                SUPPORT_MENU: [
                    MessageHandler(filters.Text("درخواست پشتیبانی/مشاوره"), request_support),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                REQUEST_SUPPORT: [
                    MessageHandler(filters.TEXT & ~filters.Text(["انصراف"]), save_support_request),
                    MessageHandler(filters.Text(["انصراف"]), support_menu),
                ],
                ABOUT_MENU: [
                    MessageHandler(filters.Text("درخواست مشاوره"), consultation_menu),
                    MessageHandler(filters.Text(BTN_BACK_TO_MAIN) | filters.Text("منوی اصلی"), start),

                ],
                FAVORITES_MENU: [
                    MessageHandler(filters.Text("◀ قبلی") | filters.Text("بعدی ▶"), navigate_favorites),
                    MessageHandler(filters.Text("🗑 حذف از علاقه‌مندی‌ها"), remove_favorite),
                    MessageHandler(filters.Text("📩 ارسال به ادمین"), send_favorite_to_admin),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                CONSULTATION: [
                    MessageHandler(filters.TEXT & ~filters.Text([BTN_BACK_TO_MAIN, "انصراف"]), save_consultation),
                    MessageHandler(filters.Text([BTN_BACK_TO_MAIN, "انصراف"]), start),
                    MessageHandler(filters.CONTACT, handle_contact),
                ],
                SERVICES_MENU: [
                    MessageHandler(filters.Text("درخواست مشاوره"), consultation_menu),
                    MessageHandler(filters.Text(BTN_BACK_TO_MAIN), start),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                    MessageHandler(filters.TEXT & ~filters.Text(BTN_BACK_TO_MAIN) & ~filters.Text("منوی اصلی") & ~filters.Text("درخواست مشاوره"), save_consultation),
                ],
            },
            fallbacks=[
                CommandHandler('start', start),
                MessageHandler(filters.ALL, fallback_handler)
            ],
            allow_reentry=True
        )
        
        application.add_handler(conv_handler)
        application.add_handler(CallbackQueryHandler(handle_copy_number, pattern="^copy_number_"))

        logger.info("✅ ربات در حال راه‌اندازی...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی ربات: {str(e)}")
        raise

if __name__ == "__main__":
    main()

    



