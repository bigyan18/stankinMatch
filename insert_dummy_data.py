import asyncio
import logging
from db import init_db, save_user_profile, UserProfile
from matching import get_embedding

# Configure logging
logging.basicConfig(level=logging.INFO)

async def insert_dummy_data():
    init_db()
    
    dummy_users = [
        {
            "user_id": 1001,
            "username": "alice_msu",
            "university": "MSU",
            "year_course": "3rd year CS",
            "skills": ["Python", "Machine Learning", "Data Analysis"],
            "interests": ["AI Research", "Chess", "Hiking"],
            "goals": "Find a partner for my ML coursework and research projects."
        },
        {
            "user_id": 1002,
            "username": "bob_itmo",
            "university": "ITMO",
            "year_course": "1st year Master",
            "skills": ["C++", "Algorithms", "Competitive Programming"],
            "interests": ["Back-end", "Gaming", "Robotics"],
            "goals": "Collaborate on competitive programming and system design."
        },
        {
            "user_id": 1003,
            "username": "charlie_msu",
            "university": "MSU",
            "year_course": "2nd year CS",
            "skills": ["JavaScript", "React", "Design"],
            "interests": ["Web Design", "Photography", "Travel"],
            "goals": "Build a startup team for a student platform."
        },
        {
            "user_id": 1004,
            "username": "dana_hse",
            "university": "HSE",
            "year_course": "4th year Econ",
            "skills": ["Statistics", "R", "English"],
            "interests": ["Finance", "Tennis", "Music"],
            "goals": "Apply data analysis to financial markets."
        },
        {
            "user_id": 1005,
            "username": "evan_spbu",
            "university": "SPbU",
            "year_course": "2nd year History",
            "skills": ["Writing", "Public Speaking", "Archaelogy"],
            "interests": ["History", "Reading", "Travel"],
            "goals": "Discuss historical research and find travel buddies."
        }
    ]
    
    for u in dummy_users:
        logging.info(f"Processing user: {u['username']}")
        
        profile_text = (
            f"University: {u['university']}. "
            f"Skills: {', '.join(u['skills'])}. "
            f"Interests: {', '.join(u['interests'])}. "
            f"Goals: {u['goals']}."
        )
        
        embedding = get_embedding(profile_text)
        
        profile = UserProfile(
            user_id=u['user_id'],
            username=u['username'],
            university=u['university'],
            year_course=u['year_course'],
            skills=u['skills'],
            interests=u['interests'],
            goals=u['goals'],
            last_updated="",
            embedding=embedding,
            is_blocked=False
        )
        
        save_user_profile(profile)
        logging.info(f"Saved profile for {u['username']}")

if __name__ == "__main__":
    asyncio.run(insert_dummy_data())
