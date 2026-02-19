from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import logging

from db import get_user_profile, get_all_profiles_except, check_rate_limit, update_rate_limit, report_user, get_user_language
from matching import compute_similarity
from strings import STRINGS

router = Router()

RATE_LIMIT_SECONDS = 3600 # 1 hour

def get_match_reason(user, match, lang: str):
    s = STRINGS[lang]
    reasons = []
    if user.university.lower() == match.university.lower():
        reasons.append(s["match_reason_uni"].format(uni=user.university))
    
    shared_skills = set(user.skills) & set(match.skills)
    if shared_skills:
        reasons.append(s["match_reason_skills"].format(skills=', '.join(list(shared_skills)[:2])))
        
    shared_interests = set(user.interests) & set(match.interests)
    if shared_interests:
        reasons.append(s["match_reason_interests"].format(interests=', '.join(list(shared_interests)[:2])))
        
    if not reasons:
        reasons.append(s["match_reason_default"])
        
    return " and ".join(reasons).capitalize()

@router.message(Command("matches"))
async def cmd_matches(message: Message):
    await run_matches(message, message.from_user.id)

async def run_matches(event_message: Message, user_id: int):
    user_profile = get_user_profile(user_id)
    lang = user_profile.language if user_profile else get_user_language(user_id)
    s = STRINGS[lang]

    if not user_profile or not user_profile.embedding:
        return await event_message.answer(s["no_profile"])
    
    other_profiles = get_all_profiles_except(user_id)
    matches = []
    
    for other in other_profiles:
        if other.embedding:
            score = compute_similarity(user_profile.embedding, other.embedding)
            logging.info(f"Similarity score for {other.username}: {score}")
            if score > 0.1: # Threshold for matches
                matches.append((other, score))
    
    matches.sort(key=lambda x: x[1], reverse=True)
    
    if not matches:
        return await event_message.answer(s["no_matches"])
    
    await event_message.answer(s["matches_found"].format(count=len(matches)), parse_mode="Markdown")
    
    for i, (match_profile, score) in enumerate(matches, 1):
        username = f"@{match_profile.username}" if match_profile.username else "Anonymous"
        reason = get_match_reason(user_profile, match_profile, lang)
        
        text = (
            f"*Match #{i}:* {username} (similarity {score:.2f})\n"
            f"💡 _Reason:_ {reason}."
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=s["report_user"], callback_data=f"report_{match_profile.user_id}")]
        ])
        
        await event_message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("report_"))
async def process_report(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    report_user(target_id)
    lang = get_user_language(callback.from_user.id)
    await callback.answer(STRINGS[lang]["user_reported"])
    await callback.message.edit_text(callback.message.text + f"\n\n({STRINGS[lang]['report_user']})")
