from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from db import save_user_profile, get_user_profile, UserProfile, get_user_language
from matching import get_embedding
from strings import STRINGS
import logging

router = Router()

class ProfileStates(StatesGroup):
    waiting_for_university = State()
    waiting_for_year = State()
    waiting_for_skills = State()
    waiting_for_interests = State()
    waiting_for_goals = State()

@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext):
    await run_profile_wizard(message, message.from_user.id, state)

async def run_profile_wizard(event_message: Message, user_id: int, state: FSMContext):
    existing_profile = get_user_profile(user_id)
    lang = existing_profile.language if existing_profile else get_user_language(user_id)
    await state.update_data(lang=lang)
    s = STRINGS[lang]
    
    if existing_profile:
        return await event_message.answer(s["profile_exists"])
    
    await event_message.answer(
        s["ask_university"],
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ProfileStates.waiting_for_university)

async def save_and_finish(message: Message, user_id: int, state: FSMContext):
    data = await state.get_data()
    username = message.from_user.username
    
    # In case of single field edit, we might be getting goals from state or message
    goals = data.get('goals')
    if not goals and message.text and (await state.get_state()) == ProfileStates.waiting_for_goals:
        goals = message.text

    logging.info(f"Saving profile for user_id: {user_id}")
    profile_text = (
        f"University: {data['university']}. "
        f"Skills: {', '.join(data.get('skills', []))}. "
        f"Interests: {', '.join(data.get('interests', []))}. "
        f"Goals: {goals or ''}."
    )
    logging.info(f"Profile text for embedding: {profile_text}")
    
    # Compute embedding
    embedding = get_embedding(profile_text)
    if embedding:
        logging.info(f"Successfully generated embedding for user_id: {user_id} (size: {len(embedding)} bytes)")
    else:
        logging.error(f"FAILED to generate embedding for user_id: {user_id}")

    lang = data.get("lang", "en")
    s = STRINGS[lang]

    profile = UserProfile(
        user_id=user_id,
        username=username,
        university=data['university'],
        year_course=data['year_course'],
        skills=data.get('skills', []),
        interests=data.get('interests', []),
        goals=goals or "",
        last_updated="", # Set in db.py
        embedding=embedding,
        language=lang
    )
    
    save_user_profile(profile)
    logging.info(f"Profile saved to database for user_id: {user_id}")
    await state.clear()
    
    await message.answer(s["profile_updated"])

@router.message(ProfileStates.waiting_for_university)
async def process_university(message: Message, state: FSMContext):
    await state.update_data(university=message.text)
    data = await state.get_data()
    lang = data.get("lang", "en")
    s = STRINGS[lang]

    if data.get("editing_single"):
        await save_and_finish(message, message.from_user.id, state)
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1st Year" if lang == "en" else "1-й курс", callback_data="year_1"), 
             InlineKeyboardButton(text="2nd Year" if lang == "en" else "2-й курс", callback_data="year_2")],
            [InlineKeyboardButton(text="3rd Year" if lang == "en" else "3-й курс", callback_data="year_3"), 
             InlineKeyboardButton(text="4th Year" if lang == "en" else "4-й курс", callback_data="year_4")],
            [InlineKeyboardButton(text="Master's" if lang == "en" else "Магистратура", callback_data="year_master"), 
             InlineKeyboardButton(text="PhD" if lang == "en" else "Аспирантура", callback_data="year_phd")],
            [InlineKeyboardButton(text=s["cancel"], callback_data="cancel_wizard")]
        ])
        await message.answer(
            s["ask_year"].format(uni=message.text),
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await state.set_state(ProfileStates.waiting_for_year)

@router.callback_query(F.data == "cancel_wizard")
async def cb_cancel_wizard(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.clear()
    await callback.answer(STRINGS[lang]["wizard_cancelled"])
    await callback.message.edit_text(STRINGS[lang]["wizard_cancelled"])

@router.callback_query(F.data.startswith("year_"))
async def cb_year(callback: types.CallbackQuery, state: FSMContext):
    year_map_en = {
        "year_1": "1st Year", "year_2": "2nd Year",
        "year_3": "3rd Year", "year_4": "4th Year",
        "year_master": "Master's", "year_phd": "PhD"
    }
    year_map_ru = {
        "year_1": "1-й курс", "year_2": "2-й курс",
        "year_3": "3-й курс", "year_4": "4-й курс",
        "year_master": "Магистратура", "year_phd": "Аспирантура"
    }
    lang = (await state.get_data()).get("lang", "en")
    year_text = year_map_en.get(callback.data, "Other") if lang == "en" else year_map_ru.get(callback.data, "Другое")
    lang = (await state.get_data()).get("lang", "en")
    s = STRINGS[lang]
    await state.update_data(year_course=year_text)
    data = await state.get_data()
    if data.get("editing_single"):
        await save_and_finish(callback.message, callback.from_user.id, state)
    else:
        await callback.answer()
        await callback.message.edit_text(s["ask_skills"].format(year=year_text), parse_mode="Markdown")
        await state.set_state(ProfileStates.waiting_for_skills)

@router.message(ProfileStates.waiting_for_year)
async def process_year(message: Message, state: FSMContext):
    await state.update_data(year_course=message.text)
    data = await state.get_data()
    lang = data.get("lang", "en")
    if data.get("editing_single"):
        await save_and_finish(message, message.from_user.id, state)
    else:
        await message.answer(STRINGS[lang]["ask_skills"].format(year=message.text))
        await state.set_state(ProfileStates.waiting_for_skills)

@router.message(ProfileStates.waiting_for_skills)
async def process_skills(message: Message, state: FSMContext):
    skills = [s.strip() for s in message.text.split(",") if s.strip()]
    await state.update_data(skills=skills)
    data = await state.get_data()
    lang = data.get("lang", "en")
    if data.get("editing_single"):
        await save_and_finish(message, message.from_user.id, state)
    else:
        await message.answer(STRINGS[lang]["ask_interests_real"])
        await state.set_state(ProfileStates.waiting_for_interests)

@router.message(ProfileStates.waiting_for_interests)
async def process_interests(message: Message, state: FSMContext):
    interests = [i.strip() for i in message.text.split(",") if i.strip()]
    await state.update_data(interests=interests)
    data = await state.get_data()
    lang = data.get("lang", "en")
    if data.get("editing_single"):
        await save_and_finish(message, message.from_user.id, state)
    else:
        await message.answer(STRINGS[lang]["ask_goals"])
        await state.set_state(ProfileStates.waiting_for_goals)

@router.message(ProfileStates.waiting_for_goals)
async def process_goals(message: Message, state: FSMContext):
    await state.update_data(goals=message.text)
    await save_and_finish(message, message.from_user.id, state)
