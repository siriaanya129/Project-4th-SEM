from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sklearn.cluster import KMeans

# --- Daily Performance Graph Logic ---
def get_daily_performance_indices(quiz_history: List[Dict]) -> Dict:
    daily_data = defaultdict(lambda: {"accuracies": [], "efficiencies": []})
    IDEAL_TIME_PER_QUESTION = 45.0

    for quiz in quiz_history:
        date_str = quiz.get("timestamp", "")[:10]
        summary = quiz.get("scoring_summary", {})
        total_score = summary.get("total_score")
        max_score = summary.get("max_score")
        
        if total_score is not None and max_score is not None and max_score > 0:
            accuracy = (total_score / max_score)
            daily_data[date_str]["accuracies"].append(accuracy)

            time_taken = quiz.get("time_taken_seconds")
            total_questions = summary.get("total_questions")
            if time_taken and total_questions:
                time_per_q = time_taken / total_questions
                time_ratio = IDEAL_TIME_PER_QUESTION / time_per_q if time_per_q > 0 else 1
                efficiency = accuracy * time_ratio
                daily_data[date_str]["efficiencies"].append(efficiency)

    sorted_dates = sorted(daily_data.keys())
    labels, accuracy_values, efficiency_values = [], [], []

    for date in sorted_dates:
        labels.append(date)
        avg_accuracy = np.mean(daily_data[date]["accuracies"]) * 100 if daily_data[date]["accuracies"] else 0
        avg_efficiency = np.mean(daily_data[date]["efficiencies"]) * 100 if daily_data[date]["efficiencies"] else 0
        accuracy_values.append(round(avg_accuracy, 1))
        efficiency_values.append(round(avg_efficiency, 1))

    return {
        "labels": labels,
        "accuracy_index": accuracy_values,
        "efficiency_index": efficiency_values
    }

# --- START OF NEW AIML CODE TO ADD ---
def categorize_learner_profile(all_user_histories: List[Dict]) -> Dict[str, str]:
    """
    Uses K-Means clustering on ALL user data to find performance profiles
    and then maps each user to a profile.
    """
    user_performance = defaultdict(list)

    for history in all_user_histories:
        student_id = history.get("student_id")
        summary = history.get("scoring_summary", {})
        
        accuracy = summary.get("correct_answers_count", 0) / summary.get("total_questions", 1)
        
        time_taken = history.get("time_taken_seconds")
        total_questions = summary.get("total_questions")
        
        if time_taken and total_questions:
            time_per_q = time_taken / total_questions
            speed_score = min(1.5, 45 / time_per_q)
        else:
            speed_score = 1.0
            
        performance_score = (accuracy * 0.7) + ((speed_score - 1) * 0.3)
        user_performance[student_id].append(performance_score)

    if not user_performance:
        return {}

    user_averages = {user: np.mean(scores) for user, scores in user_performance.items()}
    X = np.array(list(user_averages.values())).reshape(-1, 1)

    if len(X) < 3:
        user_categories = {}
        for user, avg_score in user_averages.items():
            if avg_score > 0.85: category = "Quick Learner"
            elif avg_score < 0.6: category = "Slow Learner"
            else: category = "Average Learner"
            user_categories[user] = category
        return user_categories

    kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto').fit(X)
    
    centers = kmeans.cluster_centers_.flatten()
    sorted_centers = sorted(centers)
    label_map = {
        sorted_centers[0]: "Slow Learner",
        sorted_centers[1]: "Average Learner",
        sorted_centers[2]: "Quick Learner"
    }
    
    user_categories = {}
    for user, avg_score in user_averages.items():
        user_cluster_index = kmeans.predict(np.array([[avg_score]]))[0]
        cluster_center = kmeans.cluster_centers_[user_cluster_index][0]
        user_categories[user] = label_map[cluster_center]

    return user_categories
# --- END OF NEW AIML CODE TO ADD ---


# --- YOUR EXISTING, WORKING LEARNING PATHWAY LOGIC ---
def generate_learning_pathway(user_history: List[Dict], syllabus: Dict) -> Dict:
    """
    Generates a true hierarchical learning path based on weak areas, respecting
    the Unit -> Topic -> Subtopic structure from the syllabus.
    """
    performance_map = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'correct': 0, 'total': 0})))

    for quiz in user_history:
        # Note: The original code used question.get("unit_name"). If your quiz results
        # have the unit name at the top level, quiz.get("quiz_name") is correct.
        unit = quiz.get("quiz_name") 
        for question in quiz.get("performance_breakdown", []):
            topic = question.get("topic_name")
            subtopic = question.get("subtopic_name")
            if not unit or not topic or not subtopic:
                continue
            
            stats = performance_map[unit][topic][subtopic]
            stats['total'] += 1
            if question.get("is_correct"):
                stats['correct'] += 1

    learning_path = []
    
    for unit_name in syllabus.keys():
        if unit_name in performance_map:
            unit_data = performance_map[unit_name]
            weak_topics_in_unit = []

            for topic, topic_data in unit_data.items():
                weak_subtopics_in_topic = []
                for subtopic, stats in topic_data.items():
                    if stats['correct'] < stats['total']:
                        error_rate = 1 - (stats['correct'] / stats['total'])
                        status = "High-Priority" if error_rate >= 0.5 else "Needs Review"
                        weak_subtopics_in_topic.append({"subtopic": subtopic, "status": status})
                
                if weak_subtopics_in_topic:
                    weak_topics_in_unit.append({"topic": topic, "subtopics": weak_subtopics_in_topic})
            
            if weak_topics_in_unit:
                learning_path.append({"unit": unit_name, "topics": weak_topics_in_unit})
    
    # This simplified categorization can be replaced by the new AIML function's output
    total_correct = sum(q.get('scoring_summary', {}).get('correct_answers_count', 0) for q in user_history)
    total_qs = sum(q.get('scoring_summary', {}).get('total_questions', 0) for q in user_history)
    overall_accuracy = total_correct / total_qs if total_qs > 0 else 0
    
    user_category = "Average Learner"
    if overall_accuracy > 0.85: user_category = "Quick Learner"
    elif overall_accuracy < 0.60: user_category = "Slow Learner"
    
    return {"user_category": user_category, "learning_path": learning_path}