from aiogram.fsm.state import State, StatesGroup

class RegistrationState(StatesGroup):
    full_name = State()
    birth_date = State()
    phone_number = State()
    reason = State()
    application_text = State()

class ArizaState(StatesGroup):
    full_name = State()
    birth_date = State()
    phone_number = State()
    address = State()
    application_text = State()

class ReportState(StatesGroup):
    verify = State()
    mahalla = State()
    photos = State()
    event_name = State()
    description = State()
    event_date = State()       # sana (alohida)
    event_time = State()       # vaqt (alohida)
    datetime = State()         # ← AGAR sanani va vaqtni bir joyda olmoqchi bo‘lsangiz
    location = State()
    category = State()
    direction = State()
    youth_covered = State()
    youth_count = State()

class ApplicationState(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_birth_date = State()
    waiting_for_phone_number = State()
    waiting_for_application_text = State()
    waiting_for_address = State()