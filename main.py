import asyncio
import os
import sqlite3
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("students.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    city TEXT
)
""")
conn.commit()
conn.close()

class AddStudent(StatesGroup):
    name = State()
    age = State()
    city = State()

def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="Добавить студента"), KeyboardButton(text="Показать студентов")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Выбери действие:", reply_markup=get_main_keyboard())

@dp.message(F.text == "Добавить студента")
async def add_start(message: Message, state: FSMContext):
    await state.set_state(AddStudent.name)
    await message.answer("Введите имя студента:", reply_markup=ReplyKeyboardRemove())

@dp.message(AddStudent.name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddStudent.age)
    await message.answer("Введите возраст студента:")

@dp.message(AddStudent.age)
async def add_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите возраст числом:")
        return
    await state.update_data(age=int(message.text))
    await state.set_state(AddStudent.city)
    await message.answer("Введите город студента:")

@dp.message(AddStudent.city)
async def add_city(message: Message, state: FSMContext):
    city = message.text
    data = await state.get_data()

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (name, age, city) VALUES (?, ?, ?)",
        (data["name"], data["age"], city)
    )
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("Студент успешно добавлен!", reply_markup=get_main_keyboard())

@dp.message(F.text == "Показать студентов")
async def show_students(message: Message):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, age, city FROM students")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("Список студентов пуст.")
        return

    text = "Список студентов:\n\n"
    buttons = []
    for row in rows:
        text += f"ID: {row[0]} | Имя: {row[1]} | Возраст: {row[2]} | Город: {row[3]}\n"
        buttons.append([InlineKeyboardButton(text=f"Удалить {row[1]}", callback_data=f"del_student_{row[0]}")])

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=markup)

@dp.callback_query(F.data.startswith("del_student_"))
async def delete_student(callback: CallbackQuery):
    student_id = callback.data.replace("del_student_", "")

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

    await callback.answer("Студент удален!")
    await callback.message.edit_text("Студент успешно удален из базы данных.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())