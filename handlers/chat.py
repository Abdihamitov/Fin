from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import save_chat_message, get_chat_history, clear_chat_history
from services.ai_service import chat_with_ai

router = Router()

class ChatStates(StatesGroup):
    in_chat = State()

def chat_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑️ Очистить историю", callback_data="chat_clear")
    builder.button(text="⬅️ Выйти из чата", callback_data="chat_exit")
    builder.adjust(1)
    return builder.as_markup()

@router.callback_query(F.data == "menu_chat")
async def start_chat(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChatStates.in_chat)
    text = (
        "💬 <b>Режим чата с Финном</b>\n\n"
        "Я готов ответить на любой вопрос о финансах! Спрашивай:\n"
        "• Как составить бюджет?\n"
        "• Куда вложить деньги?\n"
        "• Как выбраться из долгов?\n"
        "• Что такое ETF?\n\n"
        "Просто напиши свой вопрос 👇"
    )
    await callback.message.edit_text(text, reply_markup=chat_keyboard(), parse_mode="HTML")

@router.message(ChatStates.in_chat)
async def process_chat_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_text = message.text

    thinking_msg = await message.answer("🤔 Финн думает...")

    await save_chat_message(user_id, "user", user_text)
    history = await get_chat_history(user_id, limit=10)

    response = await chat_with_ai(user_id, user_text, history[:-1])
    await save_chat_message(user_id, "model", response)

    await thinking_msg.delete()
    await message.answer(f"🦊 <b>Финн:</b>\n\n{response}", reply_markup=chat_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "chat_clear")
async def clear_history(callback: CallbackQuery):
    await clear_chat_history(callback.from_user.id)
    await callback.answer("✅ История чата очищена!")

@router.callback_query(F.data == "chat_exit")
async def exit_chat(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 Поговорить с Финном", callback_data="menu_chat")
    builder.button(text="🎯 Пройти задание", callback_data="menu_tasks")
    builder.button(text="📊 Мой прогресс", callback_data="menu_profile")
    builder.button(text="💡 Совет дня", callback_data="menu_tip")
    builder.button(text="ℹ️ О боте", callback_data="menu_about")
    builder.adjust(1)
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери раздел 👇",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
