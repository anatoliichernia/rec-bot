import os
import tempfile
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Авторизація Google API через змінну середовища
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not creds_json:
    raise Exception("Не знайдено GOOGLE_CREDENTIALS_JSON у змінних середовища")

with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
    temp_file.write(creds_json)
    temp_file.flush()
    credentials = ServiceAccountCredentials.from_json_keyfile_name(temp_file.name, scope)

gc = gspread.authorize(credentials)

SPREADSHEET_ID = '1_obQhP9sZL4Q5oB5V1y5mRiGwRMCYXVMXVseDe1tKPw'
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Оберіть категорію рецептів зі списку:"
    )
    await send_categories_menu(update, context)

async def send_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = sheet.get_all_records()
    categories = sorted(set(r['Категорія'].strip() for r in records))

    keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text="Оберіть категорію:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text="Оберіть категорію:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    category = query.data.strip().lower()
    records = sheet.get_all_records()

    matched = [r for r in records if r['Категорія'].strip().lower() == category]

    if not matched:
        await query.edit_message_text("За цією категорією рецептів немає.")
        return

    buttons = [
        [InlineKeyboardButton(r['Ключове слово '].strip(), url=r['Посилання на рецепт '].strip())]
        for r in matched
    ]

    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(
        text=f"Рецепти за категорією '{query.data}':",
        reply_markup=reply_markup
    )

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        raise Exception("Не знайдено TELEGRAM_TOKEN у змінних середовища")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущено...")
    app.run_polling()

if __name__ == '__main__':
    main()
