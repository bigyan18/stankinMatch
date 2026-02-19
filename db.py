import sqlite3
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class UserProfile:
    user_id: int
    username: Optional[str]
    university: str
    year_course: str
    skills: List[str]
    interests: List[str]
    goals: str
    last_updated: str
    embedding: Optional[bytes] = None
    is_blocked: bool = False
    language: str = "en"

DB_PATH = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            university TEXT,
            year_course TEXT,
            skills TEXT,
            interests TEXT,
            goals TEXT,
            last_updated TEXT,
            embedding BLOB,
            is_blocked BOOLEAN DEFAULT 0,
            language TEXT DEFAULT 'en'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limits (
            user_id INTEGER,
            command TEXT,
            last_used_at TEXT,
            PRIMARY KEY (user_id, command)
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("Database initialized with reporting and rate limiting support")

def report_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def check_rate_limit(user_id: int, command: str, limit_seconds: int) -> Optional[int]:
    """Returns seconds remaining if limited, else None."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT last_used_at FROM rate_limits WHERE user_id = ? AND command = ?', (user_id, command))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        last_used = datetime.fromisoformat(row[0])
        elapsed = (datetime.now() - last_used).total_seconds()
        if elapsed < limit_seconds:
            return int(limit_seconds - elapsed)
    return None

def update_rate_limit(user_id: int, command: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO rate_limits (user_id, command, last_used_at)
        VALUES (?, ?, ?)
    ''', (user_id, command, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT skills FROM users')
    all_skills = cursor.fetchall()
    
    skill_counts = {}
    for row in all_skills:
        skills = json.loads(row[0])
        for skill in skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
    top_skill = max(skill_counts, key=skill_counts.get) if skill_counts else "None"
    
    conn.close()
    return {
        "total_users": total_users,
        "top_skill": top_skill
    }

def save_user_profile(profile: UserProfile):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Convert lists to JSON strings
    skills_json = json.dumps(profile.skills)
    interests_json = json.dumps(profile.interests)
    
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, university, year_course, skills, interests, goals, last_updated, embedding, is_blocked, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        profile.user_id,
        profile.username,
        profile.university,
        profile.year_course,
        skills_json,
        interests_json,
        profile.goals,
        datetime.now().isoformat(),
        profile.embedding,
        profile.is_blocked,
        profile.language
    ))
    
    conn.commit()
    conn.close()

def get_user_profile(user_id: int) -> Optional[UserProfile]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return UserProfile(
            user_id=row[0],
            username=row[1],
            university=row[2],
            year_course=row[3],
            skills=json.loads(row[4]),
            interests=json.loads(row[5]),
            goals=row[6],
            last_updated=row[7],
            embedding=row[8],
            is_blocked=bool(row[9]),
            language=row[10] if len(row) > 10 else "en"
        )
    return None

def get_all_profiles_except(user_id: int) -> List[UserProfile]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id != ? AND is_blocked = 0', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    profiles = []
    for row in rows:
        profiles.append(UserProfile(
            user_id=row[0],
            username=row[1],
            university=row[2],
            year_course=row[3],
            skills=json.loads(row[4]),
            interests=json.loads(row[5]),
            goals=row[6],
            last_updated=row[7],
            embedding=row[8],
            is_blocked=bool(row[9]),
            language=row[10] if len(row) > 10 else "en"
        ))
    return profiles

def delete_user_profile(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM rate_limits WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def set_user_language(user_id: int, lang: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Use INSERT OR IGNORE to create a minimal entry if user doesn't exist yet
    cursor.execute('INSERT OR IGNORE INTO users (user_id, language) VALUES (?, ?)', (user_id, lang))
    cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
    conn.commit()
    conn.close()

def get_user_language(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "en"
