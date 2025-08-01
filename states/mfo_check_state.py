from aiogram.fsm.state import StatesGroup, State

class MFOCheckState(StatesGroup):
    waiting_for_file = State()
    waiting_for_phone_file = State()
