from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from db import get_stats

router = Router()

@router.message(Command("report"))
async def cmd_report(message: Message):
    await message.answer(
        "To report a user, please use the /report command followed by their username or ID.\n\n"
        "Example: `/report @username` or `/report 12345678`.\n"
        "Our team will review the report shortly.",
        parse_mode="Markdown"
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    stats = get_stats()
    response = (
        "📊 *Bot Statistics*\n\n"
        f"👥 *Total Users:* {stats['total_users']}\n"
        f"🔥 *Top Skill:* {stats['top_skill']}\n"
        "🚀 *Goal:* Connecting 100+ students by Demo Day!"
    )
    await message.answer(response, parse_mode="Markdown")

@router.message(Command("rules"))
async def cmd_rules(message: Message):
    rules = (
        "📜 *Community Rules*\n\n"
        "1. **Student Only**: This bot is for networking among university students.\n"
        "2. **Respect Privacy**: Do not share other users' profiles without consent.\n"
        "3. **No Spam**: Do not use the bot for advertising or mass messaging.\n"
        "4. **Be Helpful**: This is a space for collaboration and growth.\n\n"
        "Failure to follow rules may lead to a permanent block."
    )
    await message.answer(rules, parse_mode="Markdown")
