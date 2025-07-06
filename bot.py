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

# Підключення до Google Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive.file',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(credentials)

SPREADSHEET_ID = '1_obQhP9sZL4Q5oB5V1y5mRiGwRMCYXVMXVseDe1tKPw'
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Ось доступні категорії рецептів. Оберіть, будь ласка:"
    )
    await send_categories_menu(update, context)

# Меню з категоріями
async def send_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = sheet.get_all_records()
    categories = sorted(set(r['Категорія'].strip() for r in records))

    keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text="Оберіть категорію:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text="Оберіть категорію:", reply_markup=reply_markup)

# Обробка вибору категорії — показ рецептів як кнопки
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
        text=f"Рецепти за категорією '{category}':",
        reply_markup=reply_markup
    )

# Запуск бота
def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == '__main__':
    main()