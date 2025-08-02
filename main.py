import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
from datetime import datetime
from config import BOT_TOKEN, ADMIN_GROUP_ID, YOSHLAR_DAFTARI_URL
from keyboards import main_keyboard as main_menu, back_to_main_menu, direction_keyboard, mahalla_keyboard
from states import ArizaState
from aiogram.dispatcher import FSMContext
from states import ReportState
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.permissions import is_user_allowed
import os
import openpyxl
from utils.excel_writer import save_report_to_excel
from dotenv import load_dotenv
from aiogram.utils.executor import (start_webhook)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# Webhook sozlamalari
WEBHOOK_HOST = "https://mahalla-yetakchisi-bot.onrender.com"  # 👈 Render project URL
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 5000))

# === START ===
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("🔙 Asosiy menyu", reply_markup=main_menu)

# === 1. ARIZA QOLDIRISH ===
@dp.message_handler(lambda msg: msg.text == "🖊 Ariza qoldirish")
async def ariza_start(message: types.Message):
    await message.answer("Iltimos, F.I.O ni kiriting, (masalan Abdullayev Abdulla Abdulla o'g'li):")
    await ArizaState.full_name.set()

@dp.message_handler(state=ArizaState.full_name)
async def ariza_fullname(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Tug‘ilgan sanangizni kiriting (kun.oy.yil):")
    await ArizaState.birth_date.set()

@dp.message_handler(state=ArizaState.birth_date)
async def ariza_birthdate(message: types.Message, state: FSMContext):
    await state.update_data(birth_date=message.text)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📞 Raqamni yuborish", request_contact=True))
    await message.answer("Telefon raqamingizni kontakt orqali yuboring:", reply_markup=keyboard)
    await ArizaState.phone_number.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=ArizaState.phone_number)
async def ariza_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone_number=phone)
    await message.answer("Yashash manzilingizni kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await ArizaState.address.set()

@dp.message_handler(state=ArizaState.address)
async def ariza_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("Murojaat matningizni yozing:")
    await ArizaState.application_text.set()

@dp.message_handler(state=ArizaState.application_text)
async def ariza_matni(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = (
        f"*Yangi ariza:*\n\n"
        f"👤 F.I.O: {data['full_name']}\n"
        f"🎂 Tug‘ilgan sana: {data['birth_date']}\n"
        f"📞 Telefon: {data['phone_number']}\n"
        f"🏠 Yashash manzili: {data['address']}\n"
        f"📝 Ariza matni: {message.text}"
    )
    await bot.send_message(ADMIN_GROUP_ID, text, parse_mode="Markdown")

    await message.answer("✅ Arizangiz yuborildi.\n\n🔙 Asosiy menyu", reply_markup=main_menu)
    await state.finish()

# ============ SHABLON HISOBOT, MAHALLA, YO‘NALISHLAR KIRITILADI =============
# (Hisobot topshirish va yetakchi haqida bo‘limlar alohida yozilgan bo‘ladi)

@dp.message_handler(lambda msg: msg.text == "📝 Hisobot topshirish")
async def report_start(message: types.Message):
    await message.answer("📲 Iltimos, telefon raqamingizni yuboring:",
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
                             KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)
                         ))
    await ReportState.check_permission.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=ReportState.check_permission)
async def check_user_permission(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"
    if is_user_allowed(phone):
        await state.update_data(phone=phone)
        await message.answer("✅ Ruxsat berildi. Mahallani tanlang:", reply_markup=mahalla_keyboard)
        await ReportState.select_mahalla.set()
    else:
        await message.answer("❌ Kechirasiz, sizga hisobot topshirish ruxsat berilmagan.")
        await state.finish()

    # JSON dan ma’lumot yuklash


with open("data/mahalla_xodimlari.json", "r", encoding="utf-8") as f:
    mahalla_xodimlari = json.load(f)

    # Mahalla tanlash klaviaturasi


def get_mahalla_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for nom in mahalla_xodimlari.keys():
        keyboard.insert(KeyboardButton(nom))
    keyboard.add(KeyboardButton("🔙 Asosiy menyu"))
    return keyboard


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📋 Mahalla tanlash"))
    await message.answer("Bo‘limni tanlang:", reply_markup=keyboard)


@dp.message_handler(state=ReportState.select_mahalla)
async def process_selected_mahalla(message: types.Message, state: FSMContext):
    await state.update_data(mahalla=message.text)
    await message.answer("Iltimos, tadbir yo‘nalishini tanlang:", reply_markup=direction_keyboard)
    await ReportState.select_direction.set()


@dp.message_handler(lambda message: message.text and message.text.strip() in mahalla_xodimlari)
async def show_leader_info(message: types.Message):
    print(f"[DEBUG Mahalla tanlandi:{message.text.strip()}]")
    tanlangan = message.text.strip()
    xodimlar = mahalla_xodimlari[tanlangan]
    javob = f"📍 <b>{tanlangan}</b> mahallasi uchun xodimlar:\n\n"
    for x in xodimlar:
        javob += f"👤 {x['ism']}\n📞 {x['telefon']}\n\n"
    await message.answer(javob, parse_mode='HTML')


@dp.message_handler(lambda message: message.text == "🔙 Asosiy menyu")
async def back_to_menu(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📋 Mahalla tanlash"))
    await message.answer("🔙 Asosiy menyu", reply_markup=keyboard)

@dp.message_handler(state=ReportState.select_direction)
async def process_direction(message: types.Message, state: FSMContext):
    direction = message.text
    await state.update_data(direction=direction)
    await ReportState.enter_date.set()
    await message.answer("📅 Tadbir o'tkazilgan sanani kiriting (masalan: 2025-07-29):")

@dp.message_handler(state=ReportState.waiting_for_event_date)
async def process_event_date(message: types.Message, state: FSMContext):
    print("📅 Sana kelib tushdi:", message.text)
    await state.update_data(event_date=message.text)
    await message.answer("🕐 Endi tadbir vaqti (soat)ni kiriting:")
    await ReportState.waiting_for_event_time.set()

@dp.message_handler(state=ReportState.enter_date)
async def process_date(message: types.Message, state: FSMContext):
    date_text = message.text.strip()
    await state.update_data(date=date_text)
    await ReportState.enter_event_name.set()
    await message.answer("📝 Tadbir nomini kiriting:")

@dp.message_handler(state=ReportState.enter_event_name)
async def process_event_name(message: types.Message, state: FSMContext):
    event_name = message.text.strip()
    await state.update_data(event_name=event_name)
    await ReportState.enter_description.set()
    await message.answer("📄 Tadbir haqida qisqacha ma’lumot kiriting:")

@dp.message_handler(state=ReportState.enter_description)
async def process_description(message: types.Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)
    await ReportState.enter_location.set()
    await message.answer("📍 Tadbir o‘tkazilgan joyni lokatsiya ko‘rinishida yuboring:")


@dp.message_handler(content_types=types.ContentType.LOCATION, state=ReportState.enter_location)
async def process_location(message: types.Message, state: FSMContext):
    location = message.location
    await state.update_data(location=(location.latitude, location.longitude))

    # Keyin rasmlarni qabul qilishga o‘tamiz
    await ReportState.upload_photos.set()
    await message.answer("🖼 Iltimos, tadbirga oid kamida 3 ta, ko‘pi bilan 3 ta rasm yuboring (alohida-alohida):")


# 📷 Foydalanuvchi rasm yuborganida ishlaydi
@dp.message_handler(content_types=types.ContentType.PHOTO, state=ReportState.upload_photos)
async def process_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)

    if len(photos) < 2:
        await message.answer(f"📷 {len(photos)} ta rasm olindi. Yana kamida {2 - len(photos)} ta yuboring.")
    elif 2 <= len(photos) < 3:
        await message.answer("✅ Yana rasm yuborishingiz mumkin yoki 'Yuborishni yakunlash' deb yozing.")
    else:
        await message.answer("✅ Yetarli rasm olindi. Iltimos, 'Yuborishni yakunlash' deb yozing.")


# 📍 Rasm yig‘ish tugaganda - Qamrov bosqichi
@dp.message_handler(lambda msg: msg.text.lower() == "yuborishni yakunlash", state=ReportState.upload_photos)
async def done_photo_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])

    if len(photos) < 3:
        await message.answer("❗️Kamida 3 ta rasm yuborishingiz kerak.")
        return

    await ask_youth_coverage(message, state)

async def ask_youth_coverage(message: types.Message, state: FSMContext):
    await ReportState.youth_coverage.set()
    await message.answer("👥 Tadbirda qatnashgan (qamrab olingan) yoshlar sonini kiriting. Masalan: 45")

@dp.message_handler(state=ReportState.youth_coverage)
async def process_youth_coverage(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Faqat son kiriting. Masalan: 37")
        return

    await state.update_data(youth_coverage=int(message.text))
    await finish_report(message, state)

# 👥 Qamrab olingan yoshlar sonini qabul qilish
@dp.message_handler(state=ReportState.youth_coverage)
async def process_youth_coverage(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❗️Faqat son kiriting. Masalan: 37")

    await state.update_data(youth_coverage=int(message.text))
    await finish_report(message, state)

async def finish_report(message: types.Message, state: FSMContext):
    data = await state.get_data()

    photos = data["photos"]
    mahalla = data["mahalla"]
    direction = data["direction"]
    event_date = data.get("event_date", "")
    event_time = data.get("event_time", "")
    event_name = data["event_name"]
    description = data["description"]
    youth_coverage = data.get("youth_coverage", "Nomaʼlum")
    latitude, longitude = data["location"]

    full_date = f"{event_date} {event_time}".strip()

    caption = (
        f"📍 *Mahalla:* {mahalla}\n"
        f"📚 *Yo‘nalish:* {direction}\n"
        f"🗓 *Vaqt:* {full_date}\n"
        f"🏷 *Tadbir:* {event_name}\n"
        f"📝 *Tavsif:* {description}\n"
        f"👥 *Qamrov:* {youth_coverage} nafar"
    )

    media = types.MediaGroup()
    for i, file_id in enumerate(photos[:3]):
        if i == 0:
            media.attach_photo(file_id, caption=caption, parse_mode='Markdown')
        else:
            media.attach_photo(file_id)

    await bot.send_media_group(chat_id=ADMIN_GROUP_ID, media=media)

    await state.update_data(date=full_date)  # Excel uchun

    updated_data = await state.get_data()
    save_report_to_excel(updated_data)

    await message.answer("✅ Hisobot yuborildi. Bosh menyuga qaytdingiz.", reply_markup=main_menu)
    await state.finish()

# === YOSHLAR DAFTARI URL ===
@dp.message_handler(lambda msg: msg.text == "📘 Yoshlar daftari")
async def yoshlar_daftari(message: types.Message):
    url_button = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("Saytga o‘tish", url="https://yoshlardaftari.uz/supports-2")
    )
    await message.answer("Quyidagi tugmani bosing:", reply_markup=url_button)

# === YETAKCHI HAQIDA MA‘LUMOT ===
@dp.message_handler(lambda msg: msg.text == "ℹ️ Yetakchi haqida maʼlumot")
async def yetakchi_malumot_start(message: types.Message):
    buttons = [KeyboardButton(m) for m in mahalla_xodimlari]
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)
    await message.answer("Quyidagi mahallalardan birini tanlang:", reply_markup=markup)

@dp.message_handler(lambda msg: msg.text in mahalla_xodimlari())
async def show_yetakchi_info(message: types.Message):
    mahalla = message.text
    xodimlar = mahalla_xodimlari
    text = f"📍 *{mahalla}* mahallasidagi yetakchilar:\n\n"
    for x in xodimlar:
        text += f"👤 {x['ism']}\n📱 {x['telefon']}\n\n"
    await message.answer(text, parse_mode="Markdown")

def save_report_to_excel(data):
    file_path = "data/reports.xlsx"
    if not os.path.exists(file_path):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append([
            "Vaqt", "Mahalla", "Yo‘nalish", "Tadbir", "Tavsif", "Joylashuv (lat, lon)", "Rasm1", "Rasm2", "Rasm3"
        ])
        wb.save(file_path)

    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    photos = data["photos"]

    ws.append([
        now,
        data["mahalla"],
        data["direction"],
        data["event_name"],
        data["description"],
        f"{data['location'][0]}, {data['location'][1]}",
        photos[0] if len(photos) > 0 else "",
        photos[1] if len(photos) > 1 else "",
        photos[2] if len(photos) > 2 else "",
        data.get("youth_coverge", "")
    ])
    wb.save(file_path)

# Webhook ishga tushirish
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )