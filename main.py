import logging
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv
import asyncio
from aiogram.client.default import DefaultBotProperties


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL", "https://your-default-url.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("PORT", 8000))

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

class ReportState(StatesGroup):
    location = State()
    photo = State()

def save_report_to_excel(data):
    print("Excelga yozilmoqda:", data)

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[[KeyboardButton(text="Hisobot topshirish")]]
    )
    await message.answer("Botga xush kelibsiz!", reply_markup=kb)

@router.message(ReportState.location)
async def set_location(message: Message, state: FSMContext):
    if message.location:
        await state.update_data(location=(message.location.latitude, message.location.longitude))
        await state.update_data(photos=[])
        await message.answer("3 tagacha rasm yuboring. Tugatgach /finish deb yozing.")
        await state.set_state(ReportState.photo)

@router.message(ReportState.photo)
async def get_photo(message: Message, state: FSMContext):
    if message.photo:
        data = await state.get_data()
        photos = data.get("photos", [])
        if len(photos) < 3:
            file_id = message.photo[-1].file_id
            photos.append(file_id)
            await state.update_data(photos=photos)
            await message.answer(f"{len(photos)} ta rasm qabul qilindi.")
        else:
            await message.answer("3 tagacha rasm yuborishingiz mumkin. /finish deb yozing.")
    elif message.text == "/finish":
        data = await state.get_data()
        save_report_to_excel(data)
        await message.answer("Hisobotingiz qabul qilindi. Rahmat!", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Hisobot topshirish")))
        await state.clear()

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    print("✅ Webhook o‘rnatildi:", WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    print("⛔️ Webhook o‘chirildi")

async def handle(request):
    return web.Response(text="Mahalla bot ishlayapti!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = asyncio.run(main())
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)