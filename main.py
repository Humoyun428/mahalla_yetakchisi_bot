import logging
import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import URLInputFile
from aiogram.webhook.aiohttp_server import setup_application, SimpleRequestHandler
from aiohttp import web
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from keyboard import main_keyboard, direction_keyboard, get_mahalla_keyboard, cancel_keyboard
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from states import RegistrationState, ReportState


WEBHOOK_URL = os.getenv("WEBHOOK_URL")



# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", 0))  # Fallback to 0

# File paths
ALLOWED_USERS_FILE = "users.json"
LEADERS_FILE = "mahalla_xodimlari.json"
APPLICATIONS_FILE = "arizalar.xlsx"
REPORTS_FILE = "hisobotlar.xlsx"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Load allowed users
def load_allowed_users():
    if os.path.exists(ALLOWED_USERS_FILE):
        with open(ALLOWED_USERS_FILE, "r") as f:
            return json.load(f)
    return []

# Load mahalla xodimlari
def load_leaders():
    if os.path.exists(LEADERS_FILE):
        with open(LEADERS_FILE, "r") as f:
            return json.load(f)
    return {}

@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer("Quyidagilardan birini tanlang:", reply_markup=main_menu)

# 1. ARIZA QOLDIRISH
@dp.message(F.text == "🖊 Ariza qoldirish")
async def apply_start(message: Message, state: FSMContext):
    await message.answer("Iltimos, to‘liq F.I.Sh yozing:", reply_markup=cancel_keyboard)
    await state.set_state(RegistrationState.full_name)

@dp.message(RegistrationState.full_name)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Tug‘ilgan sanangizni kiriting (kun-oy-yil):")
    await state.set_state(RegistrationState.birth_date)

@dp.message(RegistrationState.birth_date)
async def get_birth_date(message: Message, state: FSMContext):
    await state.update_data(birth_date=message.text)
    await message.answer("Telefon raqamingizni yuboring (Kontakt yuboring):", reply_markup=cancel_keyboard)
    await state.set_state(RegistrationState.phone_number)

@dp.message(RegistrationState.phone_number, F.contact)
async def get_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await message.answer("Arizangiz matnini kiriting:")
    await state.set_state(RegistrationState.application_text)

@dp.message(RegistrationState.application_text)
async def finish_application(message: Message, state: FSMContext):
    await state.update_data(application_text=message.text)
    data = await state.get_data()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Save to Excel
    row = {
        "F.I.Sh": data['full_name'],
        "Tug‘ilgan sana": data['birth_date'],
        "Telefon": data['phone'],
        "Ariza": data['application_text'],
        "Vaqti": now
    }

    df = pd.DataFrame([row])
    if os.path.exists(APPLICATIONS_FILE):
        df_existing = pd.read_excel(APPLICATIONS_FILE)
        df = pd.concat([df_existing, df], ignore_index=True)
    df.to_excel(APPLICATIONS_FILE, index=False)

    await message.answer("Arizangiz muvaffaqiyatli yuborildi.", reply_markup=main_menu)
    await state.clear()

# 2. HISOBOT TOPSHIRISH
@dp.message(F.text == "📝 Hisobot topshirish")
async def report_start(message: Message, state: FSMContext):
    phone_list = load_allowed_users()
    await message.answer("Telefon raqamingizni yuboring (Kontakt yuboring):", reply_markup=cancel_keyboard)
    await state.set_state(ReportState.verify)
@dp.message(ReportState.verify, F.contact)
async def verify_user(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    allowed = load_allowed_users()
    if phone in allowed:
        await state.update_data(phone=phone, images=[])
        await message.answer("Mahallani tanlang:", reply_markup=get_mahalla_keyboard())
        await state.set_state(ReportState.mahalla)
    else:
        await message.answer("Kechirasiz, sizga ruxsat berilmagan.")

@dp.message(ReportState.mahalla)
async def get_mahalla(message: Message, state: FSMContext):
    await state.update_data(mahalla=message.text)
    await message.answer("Iltimos, 5 tagacha rasm yuboring (1ta yuboring):")
    await state.set_state(ReportState.photos)

@dp.message(ReportState.photos, F.photo)
async def collect_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    images = data.get("images", [])
    images.append(message.photo[-1].file_id)
    await state.update_data(images=images)

    if len(images) >= 5:
        await message.answer("Hodisa nomini kiriting:")
        await state.set_state(ReportState.event_name)
    else:
        await message.answer(f"{len(images)} ta rasm qabul qilindi. Yana yuboring yoki 'Tugatdim' deb yozing.")

@dp.message(ReportState.photos, F.text.lower() == "tugatdim")
async def finish_photo_upload(message: Message, state: FSMContext):
    await message.answer("Hodisa nomini kiriting:")
    await state.set_state(ReportState.event_name)

@dp.message(ReportState.event_name)
async def get_event_name(message: Message, state: FSMContext):
    await state.update_data(event_name=message.text)
    await message.answer("Hodisa haqida qisqacha tavsif:")
    await state.set_state(ReportState.description)

@dp.message(ReportState.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Sana va vaqt (masalan: 2025-08-02 14:00):")
    await state.set_state(ReportState.datetime)

@dp.message(ReportState.datetime)
async def get_datetime(message: Message, state: FSMContext):
    await state.update_data(event_datetime=message.text)
    await message.answer("Manzilni kiriting:")
    await state.set_state(ReportState.location)

@dp.message(ReportState.location)
async def get_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await message.answer("Yo‘nalishni tanlang:", reply_markup=get_directions_keyboard())
    await state.set_state(ReportState.direction)

@dp.message(ReportState.direction)
async def get_direction(message: Message, state: FSMContext):
    await state.update_data(direction=message.text)
    await message.answer("Qamrab olingan yoshlar soni:")
    await state.set_state(ReportState.youth_covered)

@dp.message(ReportState.youth_covered)
async def finish_report(message: Message, state: FSMContext):
    await state.update_data(youth_covered=message.text)
    data = await state.get_data()

    # Excelga yozish
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = {
        "Mahalla": data['mahalla'],
        "Hodisa": data['event_name'],
        "Tavsif": data['description'],
        "Sana": data['event_datetime'],
        "Manzil": data['location'],
        "Yo‘nalish": data['direction'],
        "Yoshlar soni": data['youth_covered'],
        "Vaqt": now
    }

    df = pd.DataFrame([row])
    if os.path.exists(REPORTS_FILE):
        df_existing = pd.read_excel(REPORTS_FILE)
        df = pd.concat([df_existing, df], ignore_index=True)
    df.to_excel(REPORTS_FILE, index=False)

    # Admin guruhga yuborish
    caption = (
        f"<b>Mahalla:</b> {data['mahalla']}\n"
        f"<b>Hodisa:</b> {data['event_name']}\n"
        f"<b>Tavsif:</b> {data['description']}\n"
        f"<b>Sana:</b> {data['event_datetime']}\n"
        f"<b>Manzil:</b> {data['location']}\n"
        f"<b>Yo‘nalish:</b> {data['direction']}\n"
        f"<b>Yoshlar soni:</b> {data['youth_covered']}"
    )
    media = [await bot.get_file(file_id) for file_id in data['images']]
    for file_id in data['images']:
        await bot.send_photo(ADMIN_GROUP_ID, photo=file_id, caption=caption)

    await message.answer("Hisobot yuborildi. Rahmat!", reply_markup=main_menu)
    await state.clear()


# 3. YETAKCHI MAʼLUMOTI
@dp.message(F.text == "ℹ️ Yetakchi haqida maʼlumot")
async def leader_info(message: Message):
    await message.answer("Mahallani tanlang:", reply_markup=get_mahalla_keyboard())


@dp.message(F.text.in_(load_leaders().keys()))
async def show_leader_info(message: Message):
    mahalla = message.text
    leaders = load_leaders().get(mahalla, [])
    text = "\n\n".join([f"{l['ism']}\n📞 {l['telefon']}" for l in leaders])
    await message.answer(text or "Maʼlumot topilmadi")


# 4. YOSHLAR DAFTARI (URLga o'tish)
@dp.message(F.text == "📘 Yoshlar daftari")
async def open_url(message: Message):
    await message.answer("⬇️ Quyidagi havolani bosing:\nhttps://yoshlardaftari.uz/supports-2")


# Webhook
async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)


app = web.Application()
dp.startup.register(on_startup)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))