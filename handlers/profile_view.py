from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from db import get_user_profile, delete_user_profile, get_user_language
from handlers.profile_wizard import ProfileStates
from strings import STRINGS

router = Router()

def format_profile(profile, lang: str):
    s = STRINGS[lang]
    return (
        f"{s['my_profile_title']}\n\n"
        f"{s['uni']} {profile.university}\n"
        f"{s['year']} {profile.year_course}\n"
        f"{s['skills']} {', '.join(profile.skills)}\n"
        f"{s['interests']} {', '.join(profile.interests)}\n"
        f"{s['goals']} {profile.goals}\n\n"
        f"🕒 _Last updated: {profile.last_updated[:16].replace('T', ' ')}_"
    )

def get_edit_keyboard(lang: str):
    s = STRINGS[lang]
    buttons = [
        [InlineKeyboardButton(text=s["edit_uni"], callback_data="edit_university"), InlineKeyboardButton(text=s["edit_year"], callback_data="edit_year")],
        [InlineKeyboardButton(text=s["edit_skills"], callback_data="edit_skills"), InlineKeyboardButton(text=s["edit_interests"], callback_data="edit_interests")],
        [InlineKeyboardButton(text=s["edit_goals"], callback_data="edit_goals")],
        [InlineKeyboardButton(text=s["restart_wizard"], callback_data="edit_all")],
        [InlineKeyboardButton(text=s["delete_profile"], callback_data="confirm_delete")],
        [InlineKeyboardButton(text=s["done"], callback_data="finish_edit")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("myprofile"))
async def cmd_myprofile(message: Message):
    user_id = message.from_user.id
    profile = get_user_profile(user_id)
    lang = profile.language if profile else get_user_language(user_id)
    s = STRINGS[lang]
    
    if not profile:
        return await message.answer(s["no_profile"])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=s["edit_profile"], callback_data="open_edit_menu")],
        [InlineKeyboardButton(text=s["find_matches"], callback_data="start_matching")]
    ])
    
    await message.answer(format_profile(profile, lang), reply_markup=keyboard, parse_mode="Markdown")

@router.message(Command("edit"))
async def cmd_edit(message: Message):
    user_id = message.from_user.id
    profile = get_user_profile(user_id)
    lang = profile.language if profile else get_user_language(user_id)
    s = STRINGS[lang]
    
    if not profile:
        return await message.answer(s["no_profile"])
    
    await message.answer(
        s["edit_menu_title"],
        reply_markup=get_edit_keyboard(lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "open_edit_menu")
async def cb_open_edit(callback: CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    s = STRINGS[lang]
    await callback.answer()
    await callback.message.edit_text(
        s["edit_menu_title"],
        reply_markup=get_edit_keyboard(lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "finish_edit")
async def cb_finish_edit(callback: CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    s = STRINGS[lang]
    await callback.answer(s["done"])
    await callback.message.edit_text(s["profile_updated"])

@router.callback_query(F.data.startswith("edit_"))
async def process_edit_callback(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]
    user_id = callback.from_user.id
    profile = get_user_profile(user_id)
    
    if profile:
        await state.update_data(
            university=profile.university,
            year_course=profile.year_course,
            skills=profile.skills,
            interests=profile.interests,
            goals=profile.goals
        )
    
    lang = profile.language if profile else get_user_language(user_id)
    s = STRINGS[lang]
    await state.update_data(lang=lang)
    
    await callback.answer()
    
    if field == "all":
        await callback.message.edit_text(s["ask_university"])
        await state.set_state(ProfileStates.waiting_for_university)
        await state.update_data(editing_single=False)
    elif field == "university":
        await callback.message.edit_text(s["enter_uni"])
        await state.set_state(ProfileStates.waiting_for_university)
        await state.update_data(editing_single=True)
    elif field == "year":
        await callback.message.edit_text(s["enter_year"])
        await state.set_state(ProfileStates.waiting_for_year)
        await state.update_data(editing_single=True)
    elif field == "skills":
        await callback.message.edit_text(s["enter_skills"])
        await state.set_state(ProfileStates.waiting_for_skills)
        await state.update_data(editing_single=True)
    elif field == "interests":
        await callback.message.edit_text(s["enter_interests"])
        await state.set_state(ProfileStates.waiting_for_interests)
        await state.update_data(editing_single=True)
    elif field == "goals":
        await callback.message.edit_text(s["enter_goals"])
        await state.set_state(ProfileStates.waiting_for_goals)
        await state.update_data(editing_single=True)

@router.callback_query(F.data == "confirm_delete")
async def cb_confirm_delete(callback: CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    s = STRINGS[lang]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=s["yes_delete"], callback_data="actual_delete")],
        [InlineKeyboardButton(text=s["no_keep"], callback_data="open_edit_menu")]
    ])
    await callback.answer()
    await callback.message.edit_text(
        s["confirm_delete"],
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "actual_delete")
async def cb_actual_delete(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    delete_user_profile(user_id)
    await callback.answer(STRINGS[lang]["done"])
    await callback.message.edit_text(STRINGS[lang]["profile_deleted"], parse_mode="Markdown")
