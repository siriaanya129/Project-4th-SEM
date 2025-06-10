
#main.py


from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
import json
import os
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from . import analysis_engine
from .models import PerformanceBreakdownPayload
from . import dashboard_engine


from .config import settings
from .question_engine import QuestionEngine
from .quiz_generator_unit import UnitQuizGenerator
from .quiz_generator_grand import GrandQuizGenerator
from .syllabus_config import get_unit_names 
from .database_service import database_service
from urllib.parse import unquote 

app = FastAPI(title=settings.PROJECT_NAME)

# --- CORS Middleware ---
from fastapi.middleware.cors import CORSMiddleware

production_origin = os.getenv("FRONTEND_URL", "https://edu-connect-seven-indol.vercel.app")

app.add_middleware(
    CORSMiddleware,
     allow_origins=["http://localhost:3000", production_origin],  # Explicitly allow your frontend
    allow_credentials=True,
    allow_methods=["GET", "POST"], # Explicitly list methods
    allow_headers=["Authorization", "Content-Type"], # Explicitly list headers
)


# --- Pydantic Models ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginForm(BaseModel):
    username: str
    password: str
    remember_me: bool = False

# --- JWT and Authentication Helpers ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # ✅ Check if user still exists in MongoDB (using async-safe threadpool call)
    user_exists = await run_in_threadpool(database_service.check_username_exists, username=username)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists"
        )

    return username



# --- Initialize Engines ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_script_dir)
templates_file_path = os.path.join(backend_dir, 'data_initial', 'question_templates.json')
question_engine_instance = QuestionEngine(templates_file_path=templates_file_path)
unit_quiz_generator_instance = UnitQuizGenerator(question_engine=question_engine_instance)
grand_quiz_generator_instance = GrandQuizGenerator(question_engine=question_engine_instance)

# --- Root Test HTML ---
@app.get("/")
async def read_root_test_html():
    html_file_path = os.path.join(backend_dir, "static_test", "quiz_test.html")
    return FileResponse(html_file_path)

# --- User Management Endpoints ---
@app.post("/api/v1/users/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    result = await run_in_threadpool(database_service.create_user, username=user.username, email=user.email, password=user.password)
    if result["status"] == "error":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result["message"])
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/users/login")
async def login_for_access_token(form_data: LoginForm):
    user = await run_in_threadpool(database_service.authenticate_user, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    expires_in_minutes = 60 * 24 * 7 if form_data.remember_me else 60
    access_token_expires = timedelta(minutes=expires_in_minutes)
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/users/check-username/{username}")
async def check_username_availability(username: str):
    exists = await run_in_threadpool(database_service.check_username_exists, username=username)
    return {"username_exists": exists}

@app.get("/api/v1/users/check-email/{email}")
async def check_email_availability(email: str):
    exists = await run_in_threadpool(database_service.check_email_exists, email=email)
    return {"email_exists": exists}


# --- Dashboard Endpoints ---

@app.get("/api/v1/dashboard/graph-data")
async def get_dashboard_graph_data(
    current_user: str = Depends(get_current_user), 
    period: str = "all"
):
    """
    Provides aggregated daily performance data for the user's graph.
    Accepts a 'period' query parameter: '1d', '7d', '30d', or 'all'.
    """
    time_map = {
        "1d": 1,
        "7d": 7,
        "30d": 30,
        "all": 0  # 0 indicates no time limit
    }
    time_period_days = time_map.get(period, 0)
    
    # Step 1: Fetch the raw data from the database for the given time period
    quiz_history = await run_in_threadpool(
        database_service.get_performance_data_for_dashboard,
        username=current_user,
        time_period_days=time_period_days
    )

    # Step 2: Pass the raw data to the engine to calculate the daily indices
    graph_data = await run_in_threadpool(
        dashboard_engine.get_daily_performance_indices, # Corrected to dashboard_engine
        quiz_history=quiz_history
    )
    
    return graph_data


@app.post("/api/v1/dashboard/generate-pathway")
async def generate_user_learning_pathway(current_user: str = Depends(get_current_user)):
    """
    Triggers the full analysis pipeline to generate a personalized, hierarchical
    learning pathway based on a user's entire history.
    """
    # --- START OF EDITED/CORRECTED LOGIC ---

    # 1. Fetch history for the CURRENT user (for their specific pathway)
    current_user_history = await run_in_threadpool(
        database_service.get_full_quiz_history,
        username=current_user
    )

    if not current_user_history:
        return {"user_category": "Not Enough Data", "learning_path": []}

    # 2. Fetch history for ALL users (for the AIML model)
    all_users_history = await run_in_threadpool(
        database_service.get_full_quiz_history,
        username=None  # Pass None to get all users' data
    )

    # 3. Run AIML K-Means clustering to get categories for all users
    user_categories = await run_in_threadpool(
        dashboard_engine.categorize_learner_profile,
        all_user_histories=all_users_history
    )
    
    # Get the category for our specific current user
    current_user_category = user_categories.get(current_user, "Not Enough Data")
    
    # 4. Get the structured syllabus to pass to the DAA sorting function
    from .syllabus_config import SYLLABUS_TOPICS
    from collections import defaultdict

    unit_to_topics_map = defaultdict(list)
    for topic, details in SYLLABUS_TOPICS.items():
        unit_name = details.get("unit_name")
        if unit_name:
            unit_to_topics_map[unit_name].append(topic)
    
    # 5. Run DAA logic to generate the sorted, hierarchical pathway for the current user
    learning_path = await run_in_threadpool(
        dashboard_engine.generate_learning_pathway,
        user_history=current_user_history,
        syllabus=unit_to_topics_map
    )

    # 6. Combine the results and return
    return {
        "user_category": current_user_category,
        "learning_path": learning_path or []
    }
    # --- END OF EDITED/CORRECTED LOGIC ---

@app.get("/api/v1/performance/dashboard")
async def get_performance_dashboard(
    current_user: str = Depends(get_current_user), 
    period: str = "all"
):
    """
    Provides aggregated performance data for the user's dashboard.
    Accepts a 'period' query parameter: '1d', '7d', '30d', or 'all'.
    """
    time_map = {
        "1d": 1,
        "7d": 7,
        "30d": 30,
        "all": 0
    }
    time_period_days = time_map.get(period, 0)
    
    # This is the corrected line
    analytics_data = await run_in_threadpool(
        database_service.get_dashboard_analytics,
        username=current_user,
        time_period_days=time_period_days
    )
    
    return analytics_data

# --- Quiz Endpoints ---
@app.get("/api/v1/units", response_model=List[str])
async def get_available_units():
    return get_unit_names()

@app.get("/api/v1/quizzes/availability/{subject_name}")
async def get_quiz_availability(subject_name: str, current_user: str = Depends(get_current_user)):
    all_units = get_unit_names()
    history = await run_in_threadpool(database_service.get_user_quiz_history_summary, username=current_user)
    unique_quizzes_taken = history.get('unique_unit_quizzes_attempted', 0)
    is_grand_quiz_locked = unique_quizzes_taken < len(all_units)
    return {"units": all_units, "is_grand_quiz_locked": is_grand_quiz_locked}

@app.get("/api/v1/performance/history")
async def get_performance_history(current_user: str = Depends(get_current_user)):
    history = await run_in_threadpool(database_service.get_full_quiz_history, username=current_user)
    return history

@app.get("/api/v1/performance/history/{unit_name}")
async def get_performance_history_for_unit(unit_name: str, current_user: str = Depends(get_current_user)):
    decoded_unit_name = unquote(unit_name)  # ✅ FIXED: Correctly decode URL
    history = await run_in_threadpool(
        database_service.get_full_quiz_history_for_unit,
        username=current_user,
        unit_name=decoded_unit_name
    )
    return history

@app.post("/api/v1/performance/analyze")
async def analyze_performance_endpoint(payload: PerformanceBreakdownPayload, current_user: str = Depends(get_current_user)):
    """
    Receives a specific quiz's performance breakdown and returns a detailed
    analysis of performance by topic and subtopic.
    """
    # This calls the new analysis engine function
    analysis_result = await run_in_threadpool(
        analysis_engine.analyze_quiz_performance, 
        payload.performance_breakdown
    )
    
    return analysis_result

@app.get("/api/v1/quiz/unit/{unit_name}", response_model=Optional[List[Dict[str, Any]]])
async def get_unit_quiz_api(unit_name: str):
    decoded_unit_name = unit_name.replace("%20", " ") 
    quiz_questions = await run_in_threadpool(unit_quiz_generator_instance.generate_quiz_for_unit, decoded_unit_name)
    if not quiz_questions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not generate quiz.")
    return quiz_questions

@app.get("/api/v1/quiz/grand", response_model=Optional[List[Dict[str, Any]]])
async def get_grand_quiz_api():
    return await run_in_threadpool(grand_quiz_generator_instance.generate_grand_quiz)

# --- START OF EDITED FUNCTION ---
@app.post("/api/v1/quiz/submit/unit")
async def submit_unit_quiz_api(payload: Dict[str, Any], current_user: str = Depends(get_current_user)):
    quiz_questions = payload.get("quiz_questions")
    student_answers = payload.get("student_answers")
    time_taken = payload.get("time_taken_seconds")

    score_result = await run_in_threadpool(unit_quiz_generator_instance.score_unit_quiz, quiz_questions, student_answers)

    quiz_name = quiz_questions[0].get("unit_name", "Unknown Unit") if quiz_questions and quiz_questions[0] else "Unknown Unit"

    performance_breakdown = []
    for i, q_data in enumerate(quiz_questions):
        result_detail = score_result["detailed_results"][i]
        performance_breakdown.append({
            "template_id": q_data.get("id"),
            "topic_name": q_data.get("topic_name"),
            "subtopic_name": q_data.get("subtopic_name"),
            "difficulty_level": q_data.get("difficulty_level"),
            "difficulty_type": q_data.get("difficulty_type"),
            "is_correct": result_detail.get("is_correct"),
            "marks_obtained": result_detail.get("marks_obtained"),
            "marks_possible": result_detail.get("marks_possible")
        })

    # ✅ Clean scoring_summary without template_ids
    scoring_summary = {
        "total_score": score_result.get("total_score"),
        "max_score": score_result.get("max_score"),
        "correct_answers_count": score_result.get("correct_answers_count"),
        "total_questions": score_result.get("total_questions"),
        "difficulty_breakdown": {},
        "type_breakdown": {},
        "topics_covered": [],
        "subtopics_covered": []
    }

    topic_set = set()
    subtopic_set = set()
    for q in performance_breakdown:
        lvl = q["difficulty_level"]
        typ = q["difficulty_type"]
        scoring_summary["difficulty_breakdown"][lvl] = scoring_summary["difficulty_breakdown"].get(lvl, 0) + 1
        scoring_summary["type_breakdown"][typ] = scoring_summary["type_breakdown"].get(typ, 0) + 1
        if q["topic_name"]: topic_set.add(q["topic_name"])
        if q["subtopic_name"]: subtopic_set.add(q["subtopic_name"])

    scoring_summary["topics_covered"] = list(topic_set)
    scoring_summary["subtopics_covered"] = list(subtopic_set)

    final_document_to_save = {
        "student_id": current_user,
        "subject": "Statistics",
        "quiz_type": "Unit-Quizzes",
        "quiz_name": quiz_name,
        "timestamp": datetime.now().isoformat(),
        "time_taken_seconds": time_taken,
        "scoring_summary": scoring_summary,
        "performance_breakdown": performance_breakdown
    }

    await run_in_threadpool(database_service.save_quiz_result, final_document_to_save)
    return score_result


@app.post("/api/v1/quiz/submit/grand")
async def submit_grand_quiz_api(payload: Dict[str, Any], current_user: str = Depends(get_current_user)):
    quiz_questions = payload.get("quiz_questions")
    student_answers = payload.get("student_answers")
    time_taken = payload.get("time_taken_seconds")

    score_result = await run_in_threadpool(grand_quiz_generator_instance.score_grand_quiz, quiz_questions, student_answers)

    performance_breakdown = []
    for i, q_data in enumerate(quiz_questions):
        result_detail = score_result["detailed_results"][i]
        performance_breakdown.append({
            "template_id": q_data.get("id"),
            "topic_name": q_data.get("topic_name"),
            "subtopic_name": q_data.get("subtopic_name"),
            "difficulty_level": q_data.get("difficulty_level"),
            "difficulty_type": q_data.get("difficulty_type"),
            "is_correct": result_detail.get("is_correct"),
            "marks_obtained": result_detail.get("marks_obtained"),
            "marks_possible": result_detail.get("marks_possible")
        })

    # Build scoring_summary (no template_ids)
    total_score = score_result.get("total_score")
    max_score = score_result.get("max_score")
    correct_answers = score_result.get("correct_answers_count")
    total_questions = score_result.get("total_questions")

    difficulty_counts = {}
    type_counts = {}
    topics = set()
    subtopics = set()

    for q in performance_breakdown:
        lvl = q["difficulty_level"]
        typ = q["difficulty_type"]
        difficulty_counts[lvl] = difficulty_counts.get(lvl, 0) + 1
        type_counts[typ] = type_counts.get(typ, 0) + 1
        if q["topic_name"]: topics.add(q["topic_name"])
        if q["subtopic_name"]: subtopics.add(q["subtopic_name"])

    scoring_summary = {
        "total_score": total_score,
        "max_score": max_score,
        "correct_answers_count": correct_answers,
        "total_questions": total_questions,
        "difficulty_breakdown": difficulty_counts,
        "type_breakdown": type_counts,
        "topics_covered": list(topics),
        "subtopics_covered": list(subtopics)
    }

    final_document_to_save = {
        "student_id": current_user,
        "subject": "Statistics",
        "quiz_type": "Grand-Quiz",  # ✅ Important
        "quiz_name": "Grand Quiz",  # ✅ This is used in the path
        "timestamp": datetime.now().isoformat(),
        "time_taken_seconds": time_taken,
        "scoring_summary": scoring_summary,
        "performance_breakdown": performance_breakdown
    }

    await run_in_threadpool(database_service.save_quiz_result, final_document_to_save)
    return score_result


# --- END OF EDITED FUNCTION ---

@app.get("/api/v1/materials/{subject_name}")
async def get_study_materials(subject_name: str):
    materials_dir = os.path.join(backend_dir, "materials")
    if not os.path.exists(materials_dir):
        return []
    try:
        files = os.listdir(materials_dir)
        pdf_files = [f for f in files if f.endswith('.pdf')]
        materials_list = [{"name": pdf.replace('.pdf', '').replace('-', ' '), "url": f"/api/v1/materials/download/{pdf}"} for pdf in pdf_files]
        return materials_list
    except Exception as e:
        print(f"Error reading materials directory: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve materials.")

@app.get("/api/v1/materials/download/{file_name}")
async def download_material(file_name: str):
    file_path = os.path.join(backend_dir, "materials", file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/pdf', headers={"Content-Disposition": f"inline; filename=\"{file_name}\""})
    raise HTTPException(status_code=404, detail="File not found.")

# --- Static Files Mount ---
static_test_dir = os.path.join(backend_dir, "static_test")
if not os.path.exists(static_test_dir):
    os.makedirs(static_test_dir)
app.mount("/static_test", StaticFiles(directory=static_test_dir), name="static_test")
