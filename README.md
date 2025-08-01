#ЗАПУСК
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py


.
├── main.py                # Точка входа
├── requirements.txt       # Зависимости
├── README.md              # Инструкция
├── proxies.txt            # Прокси (для ускорения и распределения нагрузки)
├── mfo.db                 # База МФО (SQLite)
│
├── checkers/             # Логика проверки ИНН
│   ├── kz_checker.py     # Основная проверка (через Adilet)
│   ├── arrest_batch_runner.py
│   └── arrest_queue.py   # Очередь и обработка чанками
│
├── handlers/             # Хэндлеры aiogram
│   ├── arrests.py        # Обработка файлов на арест
│   └── mfo.py            # Проверка телефонов по базе МФО
│
├── states/               # FSM состояния aiogram
├── db/                   # Работа с mfo.db
├── keyboards/            # Клавиатуры
└── data/user_data/       # Временные файлы пользователей
