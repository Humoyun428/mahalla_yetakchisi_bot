from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.enums import ContentType
from keyboard import category_kb
import json
import os
from datetime import datetime
import pandas as pd

registration_router = Router()
report_router = Router()
info_router = Router()

ALLOWED_USERS_FILE = "users.json"
EXCEL_FILE = "hisobotlar.xlsx"
YETAKCHILAR_FILE = "mahalla_yetakchilari.json"

if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=[
        "Sana", "Telefon", "Mahalla", "Kategoriya", "Tadbir nomi",
        "Tavsif", "Vaqt", "Manzil", "Qamrov", "Rasmlar"
    ])
    df.to_excel(EXCEL_FILE, index=False)

# FSM holatlar
class RegistrationForm(StatesGroup):
    full_name = State()
    birth_date = State()
    phone_number = State()
    application_text = State()

class ReportForm(StatesGroup):
    verifying = State()
    mahalla = State()
    photos = State()
    category = State()
    name = State()
    description = State()
    date = State()
    time = State()
    location = State()
    coverage = State()

# ARIZA BLOKI
@registration_router.message(F.text == "Ariza qoldirish")
async def start_application(msg: Message, state: FSMContext):
    await msg.answer("Iltimos, to‘liq F.I.Sh ni yuboring:")
    await state.set_state(RegistrationForm.full_name)

@registration_router.message(RegistrationForm.full_name)
async def set_name(msg: Message, state: FSMContext):
    await state.update_data(full_name=msg.text)
    await msg.answer("Tug‘ilgan sanangizni yozing (masalan: 12.08.2000):")
    await state.set_state(RegistrationForm.birth_date)

@registration_router.message(RegistrationForm.birth_date)
async def set_birth(msg: Message, state: FSMContext):
    await state.update_data(birth_date=msg.text)
    await msg.answer("Telefon raqamingizni yozing:")
    await state.set_state(RegistrationForm.phone_number)

@registration_router.message(RegistrationForm.phone_number)
async def set_phone(msg: Message, state: FSMContext):
    await state.update_data(phone_number=msg.text)
    await msg.answer("Arizangiz matnini kiriting:")
    await state.set_state(RegistrationForm.application_text)

@registration_router.message(RegistrationForm.application_text)
async def submit_application(msg: Message, state: FSMContext):
    data = await state.get_data()
    info = (
        f"📌 <b>Yangi ariza</b>\n\n"
        f"👤 {data['full_name']}\n"
        f"📅 {data['birth_date']}\n"
        f"📞 {data['phone_number']}\n"
        f"📝 {msg.text}"
    )
    await msg.answer("✅ Arizangiz qabul qilindi. Rahmat.")
    await state.clear()

# HISOBOT BLOKI
@report_router.message(F.text == "Hisobot topshirish")
async def start_report(msg: Message, state: FSMContext):
    with open(ALLOWED_USERS_FILE, "r") as f:
        allowed_users = json.load(f)

    user_phone = msg.from_user.username or str(msg.from_user.id)
    if user_phone not in allowed_users:
        await msg.answer("⚠️ Kechirasiz, sizda hisobot topshirish uchun ruxsat yo‘q.")
        return

    await msg.answer("✅ Ruxsat tasdiqlandi.\nMahallangiz nomini kiriting:")
    await state.set_state(ReportForm.mahalla)

@report_router.message(ReportForm.mahalla)
async def set_mahalla(msg: Message, state: FSMContext):
    await state.update_data(mahalla=msg.text)
    await msg.answer("Iltimos, 3 tadan 5 tagacha rasm yuboring:")
    await state.set_state(ReportForm.photos)

@report_router.message(ReportForm.photos, F.content_type == ContentType.PHOTO)
async def collect_photos(msg: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(msg.photo[-1].file_id)

    if len(photos) >= 5:
        await msg.answer("Kategoriya tanlang:", reply_markup=category_kb())
        await state.update_data(photos=photos)
        await state.set_state(ReportForm.category)
    else:
        await msg.answer(f"{len(photos)} ta rasm qabul qilindi. Davom eting...")
        await state.update_data(photos=photos)

@report_router.message(ReportForm.category)
async def set_category(msg: Message, state: FSMContext):
    await state.update_data(category=msg.text)
    await msg.answer("Tadbir nomini yozing:")
    await state.set_state(ReportForm.name)

@report_router.message(ReportForm.name)
async def set_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("Tadbir tavsifini yozing:")
    await state.set_state(ReportForm.description)

@report_router.message(ReportForm.description)
async def set_description(msg: Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await msg.answer("Tadbir sanasini kiriting (masalan: 2025-08-03):")
    await state.set_state(ReportForm.date)

@report_router.message(ReportForm.date)
async def set_date(msg: Message, state: FSMContext):
    await state.update_data(date=msg.text)
    await msg.answer("Tadbir vaqti (masalan: 14:30):")
    await state.set_state(ReportForm.time)

@report_router.message(ReportForm.time)
async def set_time(msg: Message, state: FSMContext):
    await state.update_data(time=msg.text)
    await msg.answer("Manzilni kiriting:")
    await state.set_state(ReportForm.location)

@report_router.message(ReportForm.location)
async def set_location(msg: Message, state: FSMContext):
    await state.update_data(location=msg.text)
    await msg.answer("Qamrab olingan yoshlar soni:")
    await state.set_state(ReportForm.coverage)

@report_router.message(ReportForm.coverage)
async def submit_report(msg: Message, state: FSMContext):
    data = await state.update_data(coverage=msg.text)
    data = await state.get_data()

    photo_ids = data["photos"]
    media = [InputMediaPhoto(media=pid) for pid in photo_ids[:10]]

    text = (
        f"📊 <b>Yangi hisobot</b>\n\n"
        f"📱 {msg.from_user.username}\n"
        f"🏘 Mahalla: {data['mahalla']}\n"
        f"📅 Sana: {data['date']}\n"
        f"🕓 Vaqt: {data['time']}\n"
        f"📍 Manzil: {data['location']}\n"
        f"📂 Kategoriya: {data['category']}\n"
        f"🎯 Nomi: {data['name']}\n"
        f"📋 Tavsif: {data['description']}\n"
        f"🧒 Qamrov: {data['coverage']}\n"
    )

    # Bu yerda rasm va matn admin kanalga jo‘natiladi
    await msg.answer("✅ Hisobot qabul qilindi. Rahmat!")

    # Excelga yozish
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_row = pd.DataFrame([{
        "Sana": now,
        "Telefon": msg.from_user.username,
        "Mahalla": data["mahalla"],
        "Kategoriya": data["category"],
        "Tadbir nomi": data["name"],
        "Tavsif": data["description"],
        "Vaqt": data["time"],
        "Manzil": data["location"],
        "Qamrov": data["coverage"],
        "Rasmlar": ", ".join(photo_ids)
    }])
    new_row.to_excel(EXCEL_FILE, index=False, mode="a", header=False)

    await state.clear()

# YETAKCHI HAQIDA MA’LUMOT
@info_router.message(F.text == "Yetakchi haqida maʼlumot")
async def get_leader_info(msg: Message, state: FSMContext):
    await msg.answer("Mahallani tanlang:")
    await state.set_state("choose_mahalla")

@info_router.message(F.state == "choose_mahalla")
async def show_leader(msg: Message, state: FSMContext):
    mahalla = msg.text
    if not os.path.exists(YETAKCHILAR_FILE):
        await msg.answer("Yetakchilar ro‘yxati mavjud emas.")
        return

    with open(YETAKCHILAR_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if mahalla in data:
        name = data[mahalla]["name"]
        phone = data[mahalla]["phone"]
        await msg.answer(f"👤 {name}\n📞 {phone}")
    else:
        await msg.answer("❗️ Bunday mahalla topilmadi.")