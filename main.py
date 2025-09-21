import os

import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "/start - начать работу\n"
        "/vacancies - получить вакансии по QA и Python\n"
        "/help - показать справку"
    )
    keyboard = [['/vacancies']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "/start - начать работу\n"
        "/vacancies - получить вакансии по QA и Python\n"
        "/help - показать справку"
    )
    await update.message.reply_text(help_text)


async def fetch_vacancies(request, search_text):
    params = {"text": search_text, "per_page": 5}
    response = await request.get("https://api.hh.ru/vacancies", params=params)
    data = await response.json()
    return search_text, data.get("items", [])


async def vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("Поиск вакансий...")
        async with async_playwright() as p:
            request = await p.request.new_context()
            search_queries = ["QA", "Python"]
            tasks = [
                fetch_vacancies(request, query) for query in search_queries
            ]
            results = await asyncio.gather(*tasks)
            for search_text, vacancies_list in results:
                if vacancies_list:
                    message = f"<b>Вакансии по запросу {search_text}:</b>\n\n"
                    for i, vacancy in enumerate(vacancies_list[:5]):
                        title = vacancy.get("name", "Без названия")
                        company = vacancy.get("employer", {}).get(
                            "name", "Компания не указана"
                        )
                        url = vacancy.get("alternate_url", "#")
                        message += f"<b>{i+1}. {title}</b>\n"
                        message += f"{company}\n"
                        message += f"{url}\n\n"
                    await update.message.reply_text(message, parse_mode="HTML")
                else:
                    await update.message.reply_text(
                        f"По запросу {search_text} вакансий не найдено"
                    )
            await request.dispose()
    except Exception:
        await update.message.reply_text(
            "При поиске вакансий произошла ошибка"
        )


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("vacancies", vacancies))
    application.run_polling()


if __name__ == "__main__":
    main()
