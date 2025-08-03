from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import json

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ariza qoldirish")],
        [KeyboardButton(text="Hisobot topshirish")],
        [KeyboardButton(text="Yetakchi haqida maʼlumot")],
        [KeyboardButton(text="Yoshlar daftari")],
    ],
    resize_keyboard=True
)

category_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1. Bandlik va tadbirkorlik")],
        [KeyboardButton(text="2. Bo‘sh vaqt va ijtimoiy faollik")],
        [KeyboardButton(text="3. Taʼlim va iqtidor")],
        [KeyboardButton(text="4. Huquqiy madaniyat")],
        [KeyboardButton(text="5. Maʼnaviyat va maʼrifat")],
    ],
    resize_keyboard=True
)

def mahalla_yetakchi_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    try:
        with open("mahalla_yetakchilari.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        rows = []
        for name in data.keys():
            button = InlineKeyboardButton(text=name, callback_data=f"yetakchi_{name}")
            rows.append([button])
        keyboard.inline_keyboard = rows
    except Exception as e:
        print(f"[Keyboard error] {e}")
    return keyboard