from aiogram.fsm.state import StatesGroup, State

class WSCheckState(StatesGroup):
    choosing = State()
    manual = State()
    file = State()
