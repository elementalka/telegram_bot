from aiogram.fsm.state import State, StatesGroup

class ArrestCheckState(StatesGroup):
    waiting_for_inn_file = State()
