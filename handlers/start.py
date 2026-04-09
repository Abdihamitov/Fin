from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import get_or_create_user, get_user_stats, get_total_users
from services.ai_service import get_financial_tip

router = Router()

def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 Поговорить с Финном", callback_data="menu_chat")
    builder.button(text="🎯 Пройти задание", callback_data="menu_tasks")
    builder.button(text="📊 Мой прогресс", callback_data="menu_profile")
    builder.button(text="💡 Совет дня", callback_data="menu_tip")
    builder.button(text="ℹ️ О боте", callback_data="menu_about")
    builder.adjust(1)
    return builder.as_markup()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await get_or_create_user(user.id, user.username or "", user.full_name or "")

    text = (
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "Я — <b>Финн</b>, твой личный ИИ-наставник по финансовой грамотности 🦊💰\n\n"
        "Со мной ты научишься:\n"
        "• 💰 Грамотно управлять бюджетом\n"
        "• 🏦 Копить и приумножать деньги\n"
        "• 📈 Разбираться в инвестициях\n"
        "• 💳 Избегать долговых ловушек\n\n"
        "Выбери, с чего начнём 👇"
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("🏠 <b>Главное меню</b>\n\nВыбери раздел 👇", reply_markup=main_menu_kb(), parse_mode="HTML")

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери раздел 👇",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "menu_profile")
async def show_profile(callback: CallbackQuery):
    stats = await get_user_stats(callback.from_user.id)
    if not stats:
        await callback.answer("Сначала запустите бота командой /start")
        return

    level, xp, tasks_done = stats
    xp_to_next = 100 - (xp % 100)
    progress = (xp % 100)
    bar_filled = int(progress / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    level_titles = {
        1: "🌱 Новичок",
        2: "📚 Ученик",
        3: "💡 Знаток",
        4: "📊 Эксперт",
        5: "🏆 Мастер финансов"
    }
    title = level_titles.get(min(level, 5), "🏆 Легенда")

    text = (
        f"👤 <b>Твой профиль</b>\n\n"
        f"🎖️ Статус: <b>{title}</b>\n"
        f"⭐ Уровень: <b>{level}</b>\n"
        f"✨ Опыт: <b>{xp} XP</b>\n"
        f"📈 До следующего уровня: <b>{xp_to_next} XP</b>\n"
        f"[{bar}]\n\n"
        f"🎯 Заданий пройдено: <b>{tasks_done}</b>\n"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в меню", callback_data="back_to_menu")

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "menu_tip")
async def show_tip(callback: CallbackQuery):
    await callback.message.edit_text("⏳ Генерирую совет дня...", parse_mode="HTML")
    tip = await get_financial_tip()

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Другой совет", callback_data="menu_tip")
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        f"💡 <b>Совет дня</b>\n\n{tip}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "menu_about")
async def show_about(callback: CallbackQuery):
    total = await get_total_users()
    text = (
        "🤖 <b>О боте Финн</b>\n\n"
        "Финн — ИИ-ассистент, созданный чтобы помочь тебе разобраться в мире финансов.\n\n"
        "<b>Возможности:</b>\n"
        "💬 Живой чат о финансах\n"
        "🎯 Задачи по 8 темам\n"
        "📊 Система уровней и XP\n"
        "💡 Ежедневные советы\n\n"
        f"👥 Нас уже: <b>{total}</b> пользователей\n\n"
        "Сделано с ❤️ для твоей финансовой свободы"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в меню", callback_data="back_to_menu")

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
