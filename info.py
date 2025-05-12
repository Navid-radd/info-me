import gspread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
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
    REQUEST_WEBSITE
) = range(17)

# تنظیمات Google Sheets
scope = ["https://spreadsheets.google.com/feeds", 
        "https://www.googleapis.com/auth/drive"]

# تنظیمات پیشرفته لاگ‌گیری
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = RotatingFileHandler(
        'bot_debug.log',
        maxBytes=1024 * 1024 * 5,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

setup_logging()
logger = logging.getLogger(__name__)

# اتصال به Google Sheets
try:
    logger.info("در حال اتصال به Google Sheets...")
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "radoteam-0da92609cd4a.json", scope)
    client = gspread.authorize(creds)
    
    logger.info("در حال باز کردن اسپردشیت...")
    sheet = client.open_by_key("1w7lQNjPnNR8lHBfneWOwQGSM3KCWtUSIPChH8l8R-xs")
    
    worksheets = sheet.worksheets()
    logger.info(f"ورق‌های موجود: {[ws.title for ws in worksheets]}")

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
    logger.critical("خطای بحرانی در اتصال به Google Sheets:")
    logger.critical(str(e))
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
    context.bot.send_message(
        chat_id=1810708143,
        text=message
    )

# -------------------- دستور /start --------------------
async def start(update: Update, context: CallbackContext):
    keyboard = [
        ["وب سایت‌ها"],
        ["ربات‌های تلگرام"],
        ["نرم‌افزارهای ویندوزی"],
        ["پشتیبانی برای شما"],
        ["درخواست و مشاوره"],
        ["درباره رادوتیم"],
        ["لیست علاقه‌مندی‌ها"],
        ["خدمات متنوع"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.message:
        await update.message.reply_text(
            "سلام! به ربات نمونه کارهای نوید راد خوش آمدید. 🚀\n\n"
            "از منوی زیر انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.message.reply_text(
            "سلام! به ربات نمونه کارهای نوید راد خوش آمدید. 🚀\n\n"
            "از منوی زیر انتخاب کنید:",
            reply_markup=reply_markup
        )
    
    return MAIN_MENU

# -------------------- بخش وب‌سایت‌ها --------------------
async def websites_menu(update: Update, context: CallbackContext):
    keyboard = [
        ["فروشگاهی"],
        ["شرکتی"],
        ["رزومه"],
        ["گالری"],
        ["هزینه‌های طراحی وب‌سایت"],
        ["درخواست سایت"],
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.message:
        await update.message.reply_text(
            "دسته‌بندی وب‌سایت‌ها:",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.message.reply_text(
            "دسته‌بندی وب‌سایت‌ها:",
            reply_markup=reply_markup
        )
    
    return WEBSITES_MENU

async def website_category(update: Update, context: CallbackContext):
    category = update.message.text
    
    context.user_data['website_category'] = category
    
    websites = db["websites"].get_all_records()
    category_websites = [w for w in websites if w['Category'] == category]
    
    if not category_websites:
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
    
    nav_buttons = []
    if index > 0:
        nav_buttons.append("◀ قبلی")
    if index < len(websites) - 1:
        nav_buttons.append("بعدی ▶")
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.extend([
        ["ارسال به ادمین"],
        ["منوی وب‌سایت‌ها"],
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
    website = context.user_data['category_websites'][context.user_data['current_website_index']]
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    message = (
        f"کاربر {username} (آیدی: {user_id}) وب‌سایت زیر را درخواست داده:\n\n"
        f"عنوان: {website['Title']}\n"
        f"دسته‌بندی: {website['Category']}\n"
        f"توضیحات: {website['Description']}"
    )
    
    send_to_admin(context, message)
    await update.message.reply_text("درخواست شما به ادمین ارسال شد.")
    
    return WEBSITE_ITEM

async def show_website_prices(update: Update, context: CallbackContext):
    prices = """
💰 هزینه‌های طراحی وب‌سایت:

• وب‌سایت فروشگاهی: از 5 میلیون تومان
• وب‌سایت شرکتی: از 3 میلیون تومان
• وب‌سایت رزومه شخصی: از 2 میلیون تومان
• وب‌سایت گالری: از 4 میلیون تومان

⚠️ قیمت‌ها بسته به امکانات مورد نظر ممکن است تغییر کند.
"""
    
    keyboard = [
        ["درخواست سایت"],
        ["منوی وب‌سایت‌ها"],
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        prices,
        reply_markup=reply_markup
    )
    
    return WEBSITES_MENU

async def request_website(update: Update, context: CallbackContext):
    keyboard = [
        ["انصراف"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📝 لطفاً توضیح دهید چه نوع وب‌سایتی نیاز دارید:\n\n"
        "مثال: یک وب‌سایت فروشگاهی با امکانات پرداخت آنلاین و پنل مدیریت محصولات\n\n"
        "شماره تماس ادمین: 09158708858\n"
        "آیدی ادمین: @Admin",
        reply_markup=reply_markup
    )
    
    return REQUEST_WEBSITE

async def save_website_request(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    db["support"].append_row([
        user_id,
        username,
        "درخواست وب‌سایت",
        user_text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Pending"
    ])
    
    admin_message = (
        f"درخواست جدید وب‌سایت:\n"
        f"کاربر: {username} (آیدی: {user_id})\n\n"
        f"توضیحات:\n{user_text}"
    )
    send_to_admin(context, admin_message)
    
    keyboard = [
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ درخواست شما با موفقیت ثبت شد.\n"
        "پس از بررسی با شما تماس گرفته خواهد شد.",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

# -------------------- بخش ربات‌های تلگرام --------------------
async def telegram_bots_menu(update: Update, context: CallbackContext):
    keyboard = [
        ["درخواست ربات"],
        ["ادامه مطلب"],
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 ربات‌های تلگرام می‌توانند کسب‌وکار شما را متحول کنند!\n\n"
        "نمونه کارهای ما:\n"
        "1. ربات فروشگاهی\n"
        "2. ربات پشتیبانی\n"
        "3. ربات نظرسنجی\n"
        "4. ربات مدیریت محتوا\n\n"
        "برای مشاهده جزئیات هر ربات، گزینه «ادامه مطلب» را انتخاب کنید.",
        reply_markup=reply_markup
    )
    
    return TELEGRAM_BOTS_MENU

async def show_bot_details(update: Update, context: CallbackContext):
    if 'current_bot_index' not in context.user_data:
        context.user_data['current_bot_index'] = 0
    
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
    
    keyboard = []
    
    fav_button_text = "❌ حذف از علاقه‌مندی‌ها" if is_favorite else "⭐ افزودن به علاقه‌مندی‌ها"
    keyboard.append([fav_button_text])
    
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
    keyboard = [
        ["انصراف"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📝 لطفاً توضیح دهید چه نوع ربات تلگرامی نیاز دارید:\n\n"
        "مثال: یک ربات فروشگاهی با امکان پرداخت آنلاین، مدیریت محصولات و گزارش‌گیری\n\n"
        "شماره تماس ادمین: 09158708858\n"
        "آیدی ادمین: @Admin",
        reply_markup=reply_markup
    )
    
    return REQUEST_BOT

async def save_bot_request(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    db["support"].append_row([
        user_id,
        username,
        "درخواست ربات تلگرام",
        user_text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Pending"
    ])
    
    admin_message = (
        f"درخواست جدید ربات تلگرام:\n"
        f"کاربر: {username} (آیدی: {user_id})\n\n"
        f"توضیحات:\n{user_text}"
    )
    send_to_admin(context, admin_message)
    
    keyboard = [
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ درخواست شما با موفقیت ثبت شد.\n"
        "پس از بررسی با شما تماس گرفته خواهد شد.",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

# -------------------- بخش نرم‌افزارهای ویندوزی --------------------
async def windows_apps_menu(update: Update, context: CallbackContext):
    keyboard = [
        ["درخواست نرم‌افزار"],
        ["نمونه کارها"],
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "💻 نرم‌افزارهای ویندوزی می‌توانند کارایی کسب‌وکار شما را افزایش دهند!\n\n"
        "ما نرم‌افزارهای اختصاصی برای نیازهای خاص شما طراحی می‌کنیم.",
        reply_markup=reply_markup
    )
    
    return WINDOWS_APPS_MENU

async def show_app_details(update: Update, context: CallbackContext):
    if 'current_app_index' not in context.user_data:
        context.user_data['current_app_index'] = 0
    
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
    
    keyboard = []
    
    fav_button_text = "❌ حذف از علاقه‌مندی‌ها" if is_favorite else "⭐ افزودن به علاقه‌مندی‌ها"
    keyboard.append([fav_button_text])
    
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
    keyboard = [
        ["انصراف"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📝 لطفاً توضیح دهید چه نوع نرم‌افزار ویندوزی نیاز دارید:\n\n"
        "مثال: یک نرم‌افزار حسابداری با امکان صدور فاکتور، گزارش‌گیری و پشتیبان‌گیری\n\n"
        "شماره تماس ادمین: 09158708858\n"
        "آیدی ادمین: @Admin",
        reply_markup=reply_markup
    )
    
    return REQUEST_APP

async def save_app_request(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    db["support"].append_row([
        user_id,
        username,
        "درخواست نرم‌افزار ویندوزی",
        user_text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Pending"
    ])
    
    admin_message = (
        f"درخواست جدید نرم‌افزار ویندوزی:\n"
        f"کاربر: {username} (آیدی: {user_id})\n\n"
        f"توضیحات:\n{user_text}"
    )
    send_to_admin(context, admin_message)
    
    keyboard = [
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ درخواست شما با موفقیت ثبت شد.\n"
        "پس از بررسی با شما تماس گرفته خواهد شد.",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

# -------------------- بخش پشتیبانی --------------------
async def support_menu(update: Update, context: CallbackContext):
    keyboard = [
        ["درخواست پشتیبانی/مشاوره"],
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🔧 ما می‌توانیم سایت وردپرس شما را پشتیبانی و دیباگ کنیم!\n\n"
        "خدمات پشتیبانی ما شامل:\n"
        "- رفع مشکلات فنی\n"
        "- بهینه‌سازی سرعت\n"
        "- افزایش امنیت\n"
        "- افزودن امکانات جدید\n\n"
        "برای درخواست پشتیبانی یا مشاوره، گزینه زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return SUPPORT_MENU

async def request_support(update: Update, context: CallbackContext):
    keyboard = [
        ["انصراف"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📝 لطفاً توضیح دهید چه نوع پشتیبانی یا خدمتی نیاز دارید:\n\n"
        "مثال: نیاز به بهینه‌سازی سرعت یک سایت وردپرس دارم\n\n"
        "شماره تماس ادمین: 09158708858\n"
        "آیدی ادمین: @Admin",
        reply_markup=reply_markup
    )
    
    return REQUEST_SUPPORT

async def save_support_request(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    db["support"].append_row([
        user_id,
        username,
        "درخواست پشتیبانی",
        user_text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Pending"
    ])
    
    admin_message = (
        f"درخواست جدید پشتیبانی:\n"
        f"کاربر: {username} (آیدی: {user_id})\n\n"
        f"توضیحات:\n{user_text}"
    )
    send_to_admin(context, admin_message)
    
    keyboard = [
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ درخواست شما با موفقیت ثبت شد.\n"
        "پس از بررسی با شما تماس گرفته خواهد شد.",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

# -------------------- بخش مشاوره --------------------
async def consultation_menu(update: Update, context: CallbackContext):
    keyboard = [
        ["انصراف"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📞 برای مشاوره تخصصی در زمینه‌های زیر آماده خدمت رسانی به شما هستیم:\n\n"
        "- طراحی وب‌سایت\n"
        "- طراحی ربات تلگرام\n"
        "- طراحی نرم‌افزارهای ویندوزی\n"
        "- پشتیبانی و بهینه‌سازی\n\n"
        "لطفاً توضیح دهید چه نوع مشاوره‌ای نیاز دارید:\n\n"
        "شماره تماس ادمین: 09158708858\n"
        "آیدی ادمین: @Admin",
        reply_markup=reply_markup
    )
    
    return CONSULTATION

async def save_consultation(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name
    
    db["support"].append_row([
        user_id,
        username,
        "درخواست مشاوره",
        user_text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Pending"
    ])
    
    admin_message = (
        f"درخواست جدید مشاوره:\n"
        f"کاربر: {username} (آیدی: {user_id})\n\n"
        f"توضیحات:\n{user_text}"
    )
    send_to_admin(context, admin_message)
    
    keyboard = [
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ درخواست مشاوره شما با موفقیت ثبت شد.\n"
        "پس از بررسی با شما تماس گرفته خواهد شد.",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

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
        "✅ طراحی بیش از 50 پروژه موفق\n\n"
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
    favorites = get_user_favorites(user_id)
    
    if not favorites:
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
    
    return await show_favorite_item(update, context)

async def show_favorite_item(update: Update, context: CallbackContext):
    favorites = context.user_data['user_favorites']
    index = context.user_data['current_favorite_index']
    favorite = favorites[index]
    
    # دریافت اطلاعات آیتم از دیتابیس مربوطه
    item_type = favorite['ItemType']
    item_id = favorite['ItemID']
    
    if item_type == 'website':
        sheet = db["websites"]
        item = next((w for w in sheet.get_all_records() if w['ID'] == item_id), None)
        item_title = item['Title'] if item else "وب‌سایت (حذف شده)"
        description = item['Description'] if item else "این آیتم دیگر موجود نیست"
    elif item_type == 'telegram_bot':
        sheet = db["telegram_bots"]
        item = next((b for b in sheet.get_all_records() if b['ID'] == item_id), None)
        item_title = item['Title'] if item else "ربات تلگرام (حذف شده)"
        description = item['Description'] if item else "این آیتم دیگر موجود نیست"
    elif item_type == 'windows_app':
        sheet = db["windows_apps"]
        item = next((a for a in sheet.get_all_records() if a['ID'] == item_id), None)
        item_title = item['Title'] if item else "نرم‌افزار (حذف شده)"
        description = item['Description'] if item else "این آیتم دیگر موجود نیست"
    else:
        item_title = "آیتم ناشناخته"
        description = "نوع این آیتم شناسایی نشد"
    
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
    
    message_text = (
        f"🔖 آیتم {index + 1} از {len(favorites)}\n\n"
        f"📌 نوع: {'وب‌سایت' if item_type == 'website' else 'ربات تلگرام' if item_type == 'telegram_bot' else 'نرم‌افزار'}\n"
        f"🏷 عنوان: {item_title}\n\n"
        f"📝 توضیحات:\n{description}"
    )
    
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
            f"توضیحات: {item['Description']}"
        )
        send_to_admin(context, message)
        await update.message.reply_text("آیتم به ادمین ارسال شد!")
    else:
        await update.message.reply_text("خطا در یافتن آیتم!")
    
    return FAVORITES_MENU

async def services_menu(update: Update, context: CallbackContext):
    services = db["services"].get_all_records()
    
    services_text = "🛠 خدمات متنوع ما:\n\n"
    for service in services:
        services_text += f"• {service['Title']}: {service['Description']}\n\n"
    
    keyboard = [
        ["درخواست مشاوره"],
        ["منوی اصلی"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        services_text,
        reply_markup=reply_markup
    )
    
    return SERVICES_MENU

# -------------------- راه‌اندازی ربات --------------------
def main():
    try:
        # ساخت application جدید
        application = ApplicationBuilder().token("8108226042:AAGUY9msPTe_YTBQ6omHGmeNQbNp1ULo1bU").build()
        
        # اضافه کردن handlerها
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                MAIN_MENU: [
                    MessageHandler(filters.Text("وب سایت‌ها"), websites_menu),
                    MessageHandler(filters.Text("ربات‌های تلگرام"), telegram_bots_menu),
                    MessageHandler(filters.Text("نرم‌افزارهای ویندوزی"), windows_apps_menu),
                    MessageHandler(filters.Text("پشتیبانی برای شما"), support_menu),
                    MessageHandler(filters.Text("درخواست و مشاوره"), consultation_menu),
                    MessageHandler(filters.Text("درباره رادوتیم"), about_menu),
                    MessageHandler(filters.Text("لیست علاقه‌مندی‌ها"), favorites_menu),
                    MessageHandler(filters.Text("خدمات متنوع"), services_menu),
                ],
                WEBSITES_MENU: [
                    MessageHandler(filters.Text("فروشگاهی") | filters.Text("شرکتی") | 
                                 filters.Text("رزومه") | filters.Text("گالری"), website_category),
                    MessageHandler(filters.Text("هزینه‌های طراحی وب‌سایت"), show_website_prices),
                    MessageHandler(filters.Text("درخواست سایت"), request_website),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                WEBSITE_CATEGORY: [
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
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                TELEGRAM_BOT_DETAILS: [
                    MessageHandler(filters.Text("⭐ افزودن به علاقه‌مندی‌ها") | 
                                 filters.Text("❌ حذف از علاقه‌مندی‌ها"), toggle_bot_favorite),
                    MessageHandler(filters.Text("◀ قبلی") | filters.Text("بعدی ▶"), show_bot_details),
                    MessageHandler(filters.Text("درخواست ربات مشابه"), request_bot),
                    MessageHandler(filters.Text("منوی ربات‌ها"), telegram_bots_menu),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                REQUEST_BOT: [
                    MessageHandler(filters.TEXT & ~filters.Text("انصراف"), save_bot_request),
                    MessageHandler(filters.Text("انصراف"), telegram_bots_menu),
                ],
                WINDOWS_APPS_MENU: [
                    MessageHandler(filters.Text("نمونه کارها"), show_app_details),
                    MessageHandler(filters.Text("درخواست نرم‌افزار"), request_app),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                WINDOWS_APP_DETAILS: [
                    MessageHandler(filters.Text("⭐ افزودن به علاقه‌مندی‌ها") | 
                                 filters.Text("❌ حذف از علاقه‌مندی‌ها"), toggle_app_favorite),
                    MessageHandler(filters.Text("◀ قبلی") | filters.Text("بعدی ▶"), show_app_details),
                    MessageHandler(filters.Text("درخواست نرم‌افزار مشابه"), request_app),
                    MessageHandler(filters.Text("منوی نرم‌افزارها"), windows_apps_menu),
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
                    MessageHandler(filters.TEXT & ~filters.Text("انصراف"), save_support_request),
                    MessageHandler(filters.Text("انصراف"), support_menu),
                ],
                ABOUT_MENU: [
                    MessageHandler(filters.Text("درخواست مشاوره"), consultation_menu),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                FAVORITES_MENU: [
                    MessageHandler(filters.Text("◀ قبلی") | filters.Text("بعدی ▶"), navigate_favorites),
                    MessageHandler(filters.Text("🗑 حذف از علاقه‌مندی‌ها"), remove_favorite),
                    MessageHandler(filters.Text("📩 ارسال به ادمین"), send_favorite_to_admin),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
                CONSULTATION: [
                    MessageHandler(filters.TEXT & ~filters.Text("انصراف"), save_consultation),
                    MessageHandler(filters.Text("انصراف"), start),
                ],
                SERVICES_MENU: [
                    MessageHandler(filters.Text("درخواست مشاوره"), consultation_menu),
                    MessageHandler(filters.Text("منوی اصلی"), start),
                ],
            },
            fallbacks=[CommandHandler('start', start)],
        )
        
        application.add_handler(conv_handler)
        
        logger.info("✅ ربات در حال راه‌اندازی...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی ربات: {str(e)}")
        raise

if __name__ == "__main__":
    main()