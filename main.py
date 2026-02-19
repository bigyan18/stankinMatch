import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from db import init_db, get_user_language, set_user_language
from handlers import profile_wizard, profile_view, matching_handlers, admin_handlers
from strings import STRINGS

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize dispatcher
dp = Dispatcher()

# Include routers
dp.include_router(admin_handlers.router)
dp.include_router(profile_wizard.router)
dp.include_router(profile_view.router)
dp.include_router(matching_handlers.router)

def get_home_keyboard(lang: str = "en"):
    s = STRINGS[lang]
    buttons = [
        [InlineKeyboardButton(text=s["start_wizard"], callback_data="start_wizard")],
        [InlineKeyboardButton(text=s["find_matches"], callback_data="start_matching")],
        [InlineKeyboardButton(text=s["view_rules"], callback_data="view_rules"), InlineKeyboardButton(text=s["help"], callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_lang_keyboard():
    buttons = [
        [InlineKeyboardButton(text="English 🇺🇸", callback_data="lang_en"), 
         InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(F.data == "start_wizard")
async def cb_start_wizard(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    from handlers.profile_wizard import run_profile_wizard
    await run_profile_wizard(callback.message, callback.from_user.id, state)

@dp.callback_query(F.data == "start_matching")
async def cb_start_matching(callback: types.CallbackQuery):
    await callback.answer()
    from handlers.matching_handlers import run_matches
    await run_matches(callback.message, callback.from_user.id)

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        STRINGS["en"]["lang_select"],
        reply_markup=get_lang_keyboard()
    )

@dp.callback_query(F.data.startswith("lang_"))
async def cb_set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    set_user_language(callback.from_user.id, lang)
    await callback.answer(STRINGS[lang]["lang_changed"])
    
    s = STRINGS[lang]
    await callback.message.edit_text(
        f"{s['welcome']}\n\n{s['lang_select']}",
        reply_markup=get_home_keyboard(lang),
        parse_mode="Markdown"
    )

@dp.message(Command("language"))
async def cmd_language(message: Message):
    await message.answer(
        STRINGS["en"]["lang_select"],
        reply_markup=get_lang_keyboard()
    )

@dp.callback_query(F.data == "view_rules")
async def cb_view_rules(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_rules(callback.message)

@dp.callback_query(F.data == "help")
async def cb_help(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_help(callback.message)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    lang = get_user_language(message.from_user.id)
    help_text = (
        STRINGS[lang]["welcome"] + "\n\n"
        "📜 *Commands:*\n"
        "/start - " + ("Main Menu" if lang == "en" else "Главное меню") + "\n"
        "/profile - " + ("Create/Edit Profile" if lang == "en" else "Профиль") + "\n"
        "/matches - " + ("Find Peers" if lang == "en" else "Найти пары") + "\n"
        "/language - " + ("Change Language" if lang == "en" else "Сменить язык") + "\n"
        "/rules - " + ("Read Rules" if lang == "en" else "Правила") + "\n"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("rules"))
async def cmd_rules(message: Message):
    lang = get_user_language(message.from_user.id)
    rules_text = (
        "📜 *Rules*\n\n"
        "1. Be respectful\n"
        "2. No spam\n"
        "3. Students only"
    ) if lang == "en" else (
        "📜 *Правила*\n\n"
        "1. Будьте вежливы\n"
        "2. Без спама\n"
        "3. Только для студентов"
    )
    await message.answer(rules_text, parse_mode="Markdown")

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in .env file")
        return

    # Initialize database
    init_db()

    bot = Bot(token=BOT_TOKEN)
    logger.info("Starting bot polling for Demo Day...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Critical error during bot polling: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
