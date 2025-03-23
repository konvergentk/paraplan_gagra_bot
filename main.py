import os
import asyncio
import re
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from aiogram import Bot
from fastapi.middleware.cors import CORSMiddleware

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Нет TELEGRAM_BOT_TOKEN в переменных окружения!")

CHAT_IDS = list(map(int, os.getenv("TELEGRAM_CHAT_IDS", "").split(",")))
if not CHAT_IDS or CHAT_IDS == [""]:
    raise ValueError("Нет CHAT_IDS в переменных окружения!")

app = FastAPI()

origins = [
    "https://paraplangagra.ru",
    "https://paraplangagra.pages.dev",
    "https://www.paraplangagra.ru"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)

bot = Bot(token=TOKEN)

class BookingData(BaseModel):
    name: str
    phone: str
    date: str
    message: str = ""

async def send_message(text: str):
    for chat_id in CHAT_IDS:
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Ошибка при отправке в {chat_id}: {e}")

@app.post("/send")
async def send_booking(data: BookingData):
    name = data.name.strip()
    phone = data.phone.strip()
    date_str = data.date.strip()
    message = data.message.strip()

    # Проверка имени (только буквы и пробелы)
    name_regex = re.compile(r"^[A-Za-zА-Яа-яЁё\s]+$")
    if not name_regex.match(name):
        raise HTTPException(status_code=400, detail="Имя должно содержать только буквы и пробелы.")

    # Проверка телефона (7-20 символов, только цифры и разрешенные знаки)
    phone_regex = re.compile(r"^[\d+\-() ]{7,20}$")
    if not phone_regex.match(phone):
        raise HTTPException(status_code=400, detail="Введите корректный номер телефона.")

    # Проверка даты (не в прошлом и не больше текущего года)
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        current_year = today.year

        if selected_date < today + timedelta(days=1):
            raise HTTPException(status_code=400, detail="Выберите дату не ранее завтрашнего дня.")
        
        if selected_date.year != current_year:
            raise HTTPException(status_code=400, detail="Вы можете выбрать только даты в текущем году.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный формат даты.")

    # Формируем текст сообщения
    text = (
        f"🛫 Новая заявка на полёт!\n\n"
        f"👤 Имя: {name}\n"
        f"📞 Телефон: {phone}\n"
        f"📅 Дата: {date_str}\n"
        f"💬 Комментарий: {message or '—'}"
    )

    asyncio.create_task(send_message(text))
    return {"status": "ok", "message": "Заявка отправлена!"}
