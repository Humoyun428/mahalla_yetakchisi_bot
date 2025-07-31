from aiogram.dispatcher.filters.state import State, StatesGroup

class RegistrationState(StatesGroup):
    fio = State()
    birth_date = State()
    phone = State()
    reason = State()

class ArizaState(StatesGroup):
    full_name = State()
    birth_date = State()
    phone_number = State()
    address = State()
    application_text = State()

class ReportState(StatesGroup):
    check_permission = State()
    select_mahalla= State()
    upload_photos = State()
    select_direction = State()
    enter_date = State()
    enter_time = State()
    enter_event_name = State()
    enter_description = State()
    enter_location = State()
    waiting_for_mahalla = State()
    waiting_for_photos = State()
    waiting_for_direction = State()
    waiting_for_event_date = State()       # <== SHU YERDA!
    waiting_for_event_time = State()
    waiting_for_event_name = State()
    waiting_for_event_description = State()
    waiting_for_location = State()
    selecting_mahalla_for_info = State()
    waiting_for_addres = State()
    youth_coverage = State()

class ApplicationState(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_birth_date = State()
    waiting_for_phone_number = State()
    waiting_for_application_text = State()
    waiting_for_address = State()  # Yangi qo‘shilgan