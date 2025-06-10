# In backend/app/analysis_engine.py

from typing import List, Dict

# --- DAA Component: Greedy Approach ---

def analyze_quiz_performance(performance_breakdown: List[Dict]) -> Dict[str, Dict]:
    """
    Analyzes a user's quiz performance to provide a detailed breakdown of
    performance by topic and subtopic, including counts of total and correct questions.
    This function uses a Greedy approach by processing each question result sequentially.

    Args:
        performance_breakdown: A list of objects from the database, where each 
                               object represents a single question's result.

    Returns:
        A dictionary where keys are topic names. The value for each topic is 
        another dictionary where keys are subtopic names and values are objects
        containing 'total' and 'correct' counts.
        Example:
        {
          "Descriptive Statistics": {
            "Range Calculation": { "total": 2, "correct": 1 },
            "Finding Mean": { "total": 1, "correct": 1 }
          }
        }
    """
    
    # 1. Initialization: The main data structure to hold our analysis.
    topic_map: Dict[str, Dict] = {}

    # Check for valid input
    if not performance_breakdown:
        return {}

    # 2. Iteration and The Greedy Choice
    # Loop through every question result provided.
    for question in performance_breakdown:
        
        # Safely get the topic and subtopic names. If they don't exist, skip this question.
        topic_name = question.get("topic_name")
        subtopic_name = question.get("subtopic_name")
        if not topic_name or not subtopic_name:
            continue

        # --- Building the Structure ---
        # If this is the first time we've seen this topic, create an entry for it.
        if topic_name not in topic_map:
            topic_map[topic_name] = {}
        
        # If this is the first time we've seen this subtopic within this topic,
        # initialize its counter object.
        if subtopic_name not in topic_map[topic_name]:
            topic_map[topic_name][subtopic_name] = {"total": 0, "correct": 0}

        # --- Counting (The Greedy Action) ---
        # For each question, we make the simple, immediate decision to increment the counters.
        
        # Always increment the total count for this subtopic.
        topic_map[topic_name][subtopic_name]["total"] += 1

        # Only increment the correct count if the question was answered correctly.
        if question.get("is_correct"):
            topic_map[topic_name][subtopic_name]["correct"] += 1

    # 3. Finalization: The completed topic_map is the final result.
    return topic_map