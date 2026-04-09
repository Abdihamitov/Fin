from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import (
    add_xp, increment_tasks_done, save_task_result, get_user_stats
)
from services.ai_service import generate_task
from services.task_service import get_topics, get_topic_name

router = Router()

class TaskStates(StatesGroup):
    choosing_topic = State()
    answering = State()

def topics_keyboard():
    builder = InlineKeyboardBuilder()
    topics = get_topics()
    for key, label in topics.items():
        builder.button(text=label, callback_data=f"topic_{key}")
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()

def answer_keyboard():
    builder = InlineKeyboardBuilder()
    for letter in ["А", "Б", "В", "Г"]:
        builder.button(text=letter, callback_data=f"answer_{letter}")
    builder.adjust(4)
    return builder.as_markup()

def after_task_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 Ещё задание", callback_data="menu_tasks")
    builder.button(text="📊 Мой прогресс", callback_data="menu_profile")
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()

@router.callback_query(F.data == "menu_tasks")
async def show_topics(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskStates.choosing_topic)
    await callback.message.edit_text(
        "🎯 <b>Выбери тему задания</b>\n\nПо какой теме хочешь проверить знания? 👇",
        reply_markup=topics_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("topic_"))
async def handle_topic_choice(callback: CallbackQuery, state: FSMContext):
    topic_key = callback.data.replace("topic_", "")
    topic_name = get_topic_name(topic_key)

    stats = await get_user_stats(callback.from_user.id)
    level = stats[0] if stats else 1

    await callback.message.edit_text(f"⏳ Генерирую задание по теме <b>{topic_name}</b>...", parse_mode="HTML")

    task = await generate_task(topic_name, level)
    await state.set_state(TaskStates.answering)
    await state.update_data(task=task)

    options_text = "\n".join([
        f"<b>{k})</b> {v}" for k, v in task["options"].items()
    ])

    text = (
        f"📚 <b>Тема:</b> {topic_name}\n"
        f"⭐ <b>Уровень:</b> {level}\n\n"
        f"❓ <b>{task['question']}</b>\n\n"
        f"{options_text}\n\n"
        "Выбери правильный ответ 👇"
    )

    await callback.message.edit_text(text, reply_markup=answer_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("answer_"))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    user_answer = callback.data.replace("answer_", "")
    data = await state.get_data()
    task = data.get("task")

    if not task:
        await callback.answer("Что-то пошло не так. Попробуй ещё раз.")
        return

    correct = task["correct"]
    is_correct = user_answer == correct

    await save_task_result(callback.from_user.id, task["topic"], is_correct)

    if is_correct:
        await increment_tasks_done(callback.from_user.id)
        leveled_up, new_level = await add_xp(callback.from_user.id, 20)

        result_text = (
            f"✅ <b>Правильно! Молодец!</b>\n\n"
            f"📖 <b>Объяснение:</b>\n{task['explanation']}\n\n"
            f"🎉 <b>+20 XP</b> за правильный ответ!"
        )

        if leveled_up:
            result_text += f"\n\n🆙 <b>Новый уровень! Теперь ты {new_level} уровня!</b> 🎊"
    else:
        result_text = (
            f"❌ <b>Неправильно.</b>\n\n"
            f"Правильный ответ: <b>{correct}</b>\n\n"
            f"📖 <b>Объяснение:</b>\n{task['explanation']}\n\n"
            f"💪 Не сдавайся! Каждая ошибка — это урок!"
        )

    await state.clear()
    await callback.message.edit_text(result_text, reply_markup=after_task_keyboard(), parse_mode="HTML")
