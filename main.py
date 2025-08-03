import asyncio
import logging
from states import registration_router, report_router, RegistrationForm, ReportForm
from mahalla_info import info_router
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from states import registration_router, report_router
from keyboard import main_menu_kb
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

dp = Dispatcher()

# Routerlarni ulash
dp.include_router(registration_router)
dp.include_router(report_router)
dp.include_router(info_router)

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # /start komandasi uchun tugma
    @dp.message()
    async def on_start(message):
        if message.text == "/start":
            await message.answer("Asosiy menyu:", reply_markup=main_menu_kb())

    # Webhook uchun sozlash
    await bot.set_webhook(WEBHOOK_URL)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())