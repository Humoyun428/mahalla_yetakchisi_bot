from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import json

# 🟩 1. Asosiy menyu
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🖊 Ariza qoldirish"), KeyboardButton(text="📝 Hisobot topshirish")],
        [KeyboardButton(text="ℹ️ Yetakchi haqida maʼlumot"), KeyboardButton(text="📘 Yoshlar daftari")]
    ],
    resize_keyboard=True
)

# ↩️ Asosiy menyuga qaytish tugmasi
back_to_main_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]],
    resize_keyboard=True
)

# 🎯 Yo‘nalish tugmalari
direction_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Madaniyat va sanʼat"), KeyboardButton(text="Sport")],
        [KeyboardButton(text="AY-TI"), KeyboardButton(text="Vatanparvarlik")],
        [KeyboardButton(text="Maʼnaviyat va kitobxonlik")],
        [KeyboardButton(text="🔙 Asosiy menyu")]
    ],
    resize_keyboard=True
)

# 🏘 Mahalla tugmalari (69 ta)
def get_mahalla_keyboard() -> ReplyKeyboardMarkup:
    keyboard = []
    try:
        with open("data/mahalla_xodimlari.json", "r", encoding="utf-8") as f:
            mahalla_data = json.load(f)
            mahalla_list = list(mahalla_data.keys())
            for i in range(0, len(mahalla_list), 2):
                if i + 1 < len(mahalla_list):
                    keyboard.append([
                        KeyboardButton(text=mahalla_list[i]),
                        KeyboardButton(text=mahalla_list[i + 1])
                    ])
                else:
                    keyboard.append([KeyboardButton(text=mahalla_list[i])])
    except Exception as e:
        print("❌ Mahalla tugmalari yuklanmadi:", e)

    keyboard.append([KeyboardButton(text="🔙 Asosiy menyu")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# 🔻 Bekor qilish tugmasi
cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Bekor qilish")]],
    resize_keyboard=True
)