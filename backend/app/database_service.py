# database_service.py

import os
import pymongo
import certifi
from dotenv import load_dotenv
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Dict

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class DatabaseService:
    def __init__(self):
        # Load .env from 2 levels up (backend/.env)
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(dotenv_path)

        self.connection_string = os.getenv("MONGO_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("CRITICAL: MONGO_CONNECTION_STRING environment variable is not set.")

        try:
            print("Trying to connect to MongoDB with certifi...")
            self.client = pymongo.MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                tlsCAFile=certifi.where()
            )
            self.db = self.client.educonnect_db
            self.users_collection = self.db.users
            self.quiz_results_collection = self.db.quiz_results
            self.client.admin.command('ping')  # Force connection check
            self.quiz_results_collection.create_index("path")
            print("✅ MongoDB connected successfully.")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.client = None

    def create_user(self, username: str, email: str, password: str):
        if self.client is None:
            return {"status": "error", "message": "Database not connected."}
        if self.users_collection.find_one({"username": username}):
            return {"status": "error", "message": "Username already exists."}
        if self.users_collection.find_one({"email": email}):
            return {"status": "error", "message": "Email already registered."}

        hashed_password = pwd_context.hash(password)
        user_document = {
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "created_at": datetime.now().isoformat()
        }

        try:
            self.users_collection.insert_one(user_document)
            return {"status": "success", "message": "User created successfully."}
        except Exception:
            return {"status": "error", "message": "Could not create user."}

    def authenticate_user(self, username: str, password: str):
        user = self.users_collection.find_one({"username": username})
        if not user or not pwd_context.verify(password, user["password_hash"]):
            return False
        return user

    def check_username_exists(self, username: str) -> bool:
        if self.client is None:
            return False
        return self.users_collection.find_one({"username": username}) is not None

    def check_email_exists(self, email: str) -> bool:
        if self.client is None:
            return False
        return self.users_collection.find_one({"email": email}) is not None

    def get_user_quiz_history_summary(self, username: str) -> dict:
        if self.client is None:
            return {'unique_unit_quizzes_attempted': 0}
        distinct_quizzes = self.quiz_results_collection.distinct(
            'quiz_name',
            {'student_id': username, 'quiz_type': 'Unit-Quizzes'}
        )
        return {'unique_unit_quizzes_attempted': len(distinct_quizzes)}

    def save_quiz_result(self, result_data: dict):
        if self.client is None:
            return {"status": "error", "message": "Database not connected."}

        student_id = result_data.get("student_id")
        subject = result_data.get("subject")
        quiz_type = result_data.get("quiz_type")
        quiz_name = result_data.get("quiz_name")
        timestamp = result_data.get("timestamp") or datetime.now().isoformat()
        performance = result_data.get("performance_breakdown")
        time_taken = result_data.get("time_taken_seconds", None)

        total_score = sum(q.get("marks_obtained", 0) for q in performance)
        max_score = sum(q.get("marks_possible", 0) for q in performance)
        correct_answers = sum(1 for q in performance if q.get("is_correct"))

        difficulty_counts = {}
        type_counts = {}
        topics = set()
        subtopics = set()

        for q in performance:
            difficulty = q.get("difficulty_level", "unknown")
            dtype = q.get("difficulty_type", "unknown")
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
            type_counts[dtype] = type_counts.get(dtype, 0) + 1
            if q.get("topic_name"): topics.add(q["topic_name"])
            if q.get("subtopic_name"): subtopics.add(q["subtopic_name"])

        scoring_summary = {
            "total_score": total_score,
            "max_score": max_score,
            "correct_answers_count": correct_answers,
            "total_questions": len(performance),
            "difficulty_breakdown": difficulty_counts,
            "type_breakdown": type_counts,
            "topics_covered": list(topics),
            "subtopics_covered": list(subtopics)
        }

        path = f"{student_id}/{subject}/{'Grand-Quiz' if quiz_type == 'Grand-Quiz' else quiz_name}/{timestamp}"

        doc_to_store = {
            "path": path,
            "student_id": student_id,
            "subject": subject,
            "quiz_type": quiz_type,
            "quiz_name": quiz_name,
            "timestamp": timestamp,
            "performance_breakdown": performance,
            "time_taken_seconds": time_taken,
            "scoring_summary": scoring_summary
        }

        try:
            self.quiz_results_collection.insert_one(doc_to_store)
            return {"status": "success", "message": "Quiz result saved with structured path."}
        except Exception as e:
            print(f"Error saving quiz result: {e}")
            return {"status": "error", "message": "Could not save quiz result."}

    def get_full_quiz_history(self, username: str = None) -> List[Dict]:
        if self.client is None:
            return []
        query = {}
        if username:
            query["student_id"] = username

        cursor = self.quiz_results_collection.find(
            query,
            {"_id": 0}
        ).sort("timestamp", pymongo.DESCENDING)
        return list(cursor)

    def get_full_quiz_history_for_unit(self, username: str, unit_name: str) -> List[Dict]:
        if self.client is None:
            return []
        cursor = self.quiz_results_collection.find(
            {"student_id": username, "quiz_name": unit_name},
            {"_id": 0}
        ).sort("timestamp", pymongo.DESCENDING)
        return list(cursor)
    
    
    def get_dashboard_analytics(self, username: str, time_period_days: int) -> Dict:
        """
        Fetches and aggregates user performance data for the dashboard view.
        Filters by a specific time period.
        """
        if self.client is None:
            return {}
        
        # --- Date Filtering Logic ---
        query = {"student_id": username}
        if time_period_days > 0:
            # Calculate the date to filter from
            start_date = datetime.now() - timedelta(days=time_period_days)
            # Add the date condition to the MongoDB query
            query["timestamp"] = {"$gte": start_date.isoformat()}

        # Fetch all relevant quiz results within the time period
        quiz_results = list(self.quiz_results_collection.find(query))

        # --- Aggregation Logic (DAA - Iteration/Counting) ---
        # This will hold our 3x3 grid data, e.g., dashboard_data['easy']['direct']
        dashboard_data = {}
        
        # Define the categories for the grid
        levels = ["easy", "medium", "hard"]
        types = ["direct", "logical reasoning", "aptitude"]

        # Initialize the grid structure
        for level in levels:
            dashboard_data[level] = {}
            for type_ in types:
                dashboard_data[level][type_] = {"total": 0, "correct": 0}

        # Loop through every question from every fetched quiz
        for result in quiz_results:
            for question in result.get("performance_breakdown", []):
                level = question.get("difficulty_level", "unknown")
                type_ = question.get("difficulty_type", "unknown")

                # Check if the category is one we are tracking
                if level in levels and type_ in types:
                    dashboard_data[level][type_]["total"] += 1
                    if question.get("is_correct"):
                        dashboard_data[level][type_]["correct"] += 1
        
        return dashboard_data


    def get_performance_data_for_dashboard(self, username: str, time_period_days: int) -> List[Dict]:
            """
            Fetches all quiz results for a user within a specific time period.
            If time_period_days is 0, it fetches all results.
            """
            if self.client is None:
                return []

            # The base query always filters by the current user
            query = {"student_id": username}

            # If a time period is specified (not 'all time'), add a date filter
            if time_period_days > 0:
                # Calculate the date to start filtering from
                start_date = datetime.now() - timedelta(days=time_period_days)
                # Add the date condition to the MongoDB query.
                # '$gte' means "greater than or equal to".
                query["timestamp"] = {"$gte": start_date.isoformat()}
            
            # Execute the query to find all matching documents
            cursor = self.quiz_results_collection.find(query, {"_id": 0})
            
            return list(cursor)
    
    
# Instantiate globally
database_service = DatabaseService()
