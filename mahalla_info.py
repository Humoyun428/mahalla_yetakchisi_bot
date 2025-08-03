from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboard import mahalla_yetakchi_kb
import json

info_router = Router()

# "Yetakchi haqida maʼlumot" tugmasi bosilganda
@info_router.message(F.text.lower() == "yetakchi haqida maʼlumot")
async def yetakchi_malumot_start(message: Message, state: FSMContext):
    await message.answer("Iltimos, mahallani tanlang:", reply_markup=mahalla_yetakchi_kb())

# Mahalla tugmasi bosilganda
@info_router.callback_query(F.data.startswith("yetakchi_"))
async def show_yetakchi_info(callback: CallbackQuery):
    mahalla_nomi = callback.data.replace("yetakchi_", "")
    try:
        with open("mahalla_yetakchilari.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        if mahalla_nomi in data:
            info = data[mahalla_nomi]
            await callback.message.answer(
                f"📍 <b>{mahalla_nomi}</b> mahallasi yetakchisi:\n\n"
                f"👤 {info['ism']}\n"
                f"📞 {info['telefon']}",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer("Ushbu mahalla uchun maʼlumot topilmadi.")
    except Exception as e:
        await callback.message.answer("Xatolik yuz berdi. Admin bilan bog‘laning.")
        print(f"[ERROR] {e}")