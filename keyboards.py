from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Asosiy menyu tugmalari
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(
    KeyboardButton("🖊 Ariza qoldirish"),
    KeyboardButton("📝 Hisobot topshirish")
).add(
    KeyboardButton("ℹ️ Yetakchi haqida maʼlumot"),
    KeyboardButton("📘 Yoshlar daftari")
)

# ↩️ Asosiy menyuga qaytish tugmasi
back_to_main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
back_to_main_menu.add(KeyboardButton("🔙 Asosiy menyu"))

# 🎯 Yo‘nalish tugmalari
direction_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
direction_keyboard.add(
    KeyboardButton("Madaniyat va sanʼat"),
    KeyboardButton("Sport"),
    KeyboardButton("AY-TI"),
    KeyboardButton("Vatanparvarlik"),
    KeyboardButton("Maʼnaviyat va kitobxonlik")
).add(KeyboardButton("🔙 Asosiy menyu"))

# 🏘️ Mahalla tugmalari (69 ta mahallani yuklagan bo‘lsangiz avtomatik yuklanadi)
import json

mahalla_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

try:
    with open("data/mahalla_xodimlari.json", "r", encoding="utf-8") as f:
        mahalla_data = json.load(f)
        rows = list(mahalla_data.keys())
        for i in range(0, len(rows), 2):
            if i + 1 < len(rows):
                mahalla_keyboard.add(KeyboardButton(rows[i]), KeyboardButton(rows[i + 1]))
            else:
                mahalla_keyboard.add(KeyboardButton(rows[i]))
    mahalla_keyboard.add(KeyboardButton("🔙 Asosiy menyu"))
except Exception as e:
    print("❌ Mahalla tugmalari yuklanmadi:", e)