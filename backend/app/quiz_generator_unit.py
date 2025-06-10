import random
import os
from typing import List, Dict, Any, Optional

from .question_engine import QuestionEngine
from .syllabus_config import get_unit_names, get_topics_for_unit # To get topics for a unit

class UnitQuizGenerator:
    def __init__(self, question_engine: QuestionEngine):
        self.question_engine = question_engine
        self.all_templates = self.question_engine.get_all_templates()
        if not self.all_templates:
            print("CRITICAL WARNING: No question templates loaded into QuestionEngine. UnitQuizGenerator will not function.")

    def _select_templates_for_unit_quiz(self, unit_name: str) -> List[Dict[str, Any]]:
        """
        Selects 15 question templates for a unit quiz based on specified rules.
        - 10 direct (1 mark each)
        - 5 from (aptitude / logical reasoning) (2 marks each)
        """
        
        unit_templates = [
            tpl for tpl in self.all_templates 
            if tpl.get("unit_name") == unit_name
        ]

        if not unit_templates:
            print(f"Warning: No question templates found for unit '{unit_name}'.")
            return []

        # Shuffle the unit_templates RANDOMLY before splitting by type
        # This is a key step to ensure variety in which templates are considered first.
        random.shuffle(unit_templates)

        direct_templates = [t for t in unit_templates if t.get("difficulty_type") == "direct"]
        aptitude_templates = [t for t in unit_templates if t.get("difficulty_type") == "aptitude"]
        logical_templates = [t for t in unit_templates if t.get("difficulty_type") == "logical reasoning"]
        
        # No need to shuffle these sub-lists again if unit_templates was already shuffled,
        # but it doesn't hurt and can make logic clearer if you prefer:
        # random.shuffle(direct_templates)
        # random.shuffle(aptitude_templates)
        # random.shuffle(logical_templates)

        potential_two_mark_templates = aptitude_templates + logical_templates
        random.shuffle(potential_two_mark_templates) # Shuffle the combined list too

        selected_template_objects = [] 
        selected_ids = set()

        # 1. Select 10 direct questions (1 mark)
        count_direct = 0
        for tpl in direct_templates: # Iterating through a now shuffled list
            if count_direct < 10 and tpl["id"] not in selected_ids:
                selected_template_objects.append({"template": tpl, "marks": 1})
                selected_ids.add(tpl["id"])
                count_direct += 1
        
        direct_needed = 10 - count_direct
        if direct_needed > 0 and direct_templates:
            available_direct = [t for t in direct_templates if t["id"] not in selected_ids] # Prefer unique
            if len(available_direct) < direct_needed: # Not enough unique, allow reuse
                available_direct.extend(random.choices(direct_templates, k=direct_needed - len(available_direct)))
            
            chosen_fillers = random.sample(available_direct, min(direct_needed, len(available_direct)))
            for tpl in chosen_fillers:
                 selected_template_objects.append({"template": tpl, "marks": 1})
                 # selected_ids.add(tpl["id"]) # Don't add to selected_ids if allowing reuse for filling strictly

        # 2. Select 5 aptitude/logical questions (2 marks each)
        count_two_mark = 0
        for tpl in potential_two_mark_templates: # Iterating through a now shuffled list
            if count_two_mark < 5 and tpl["id"] not in selected_ids:
                selected_template_objects.append({"template": tpl, "marks": 2})
                selected_ids.add(tpl["id"])
                count_two_mark += 1
        
        two_mark_needed = 5 - count_two_mark
        if two_mark_needed > 0 and potential_two_mark_templates:
            available_two_mark = [t for t in potential_two_mark_templates if t["id"] not in selected_ids]
            if len(available_two_mark) < two_mark_needed:
                available_two_mark.extend(random.choices(potential_two_mark_templates, k=two_mark_needed - len(available_two_mark)))
            
            chosen_fillers = random.sample(available_two_mark, min(two_mark_needed, len(available_two_mark)))
            for tpl in chosen_fillers:
                 selected_template_objects.append({"template": tpl, "marks": 2})


        # If still not 15 questions, this indicates a severe lack of templates.
        if len(selected_template_objects) < 15:
            print(f"Warning: Selected {len(selected_template_objects)}/15 templates for unit '{unit_name}'. Quiz will be shorter or have repeats from general pool.")
            # Fallback: Fill with any remaining unique templates from the unit, then allow repeats
            all_unit_templates_pool = [t for t in unit_templates if t["id"] not in selected_ids] # Prefer unique
            
            while len(selected_template_objects) < 15:
                if not all_unit_templates_pool: # No more unique templates from this unit
                    # Fallback to any template from the unit (allowing repeats of already selected template IDs)
                    if not unit_templates: break # No templates for this unit at all
                    all_unit_templates_pool = unit_templates 
                
                if not all_unit_templates_pool: break # Still no templates

                tpl = random.choice(all_unit_templates_pool)
                # Decide marks: try to fulfill the 1-mark vs 2-mark counts
                current_one_mark_count = sum(1 for item in selected_template_objects if item['marks']==1)
                mark_to_assign = 1 if current_one_mark_count < 10 else 2
                selected_template_objects.append({"template": tpl, "marks": mark_to_assign })
                if tpl in all_unit_templates_pool and tpl["id"] in selected_ids: # If reusing, try to remove from pool to get others
                    try: all_unit_templates_pool.remove(tpl)
                    except ValueError: pass # already removed

        random.shuffle(selected_template_objects) # Shuffle the final list of questions for presentation order
        return selected_template_objects[:15]
    
    
    def generate_quiz_for_unit(self, unit_name: str) -> Optional[List[Dict[str, Any]]]:
        selected_items = self._select_templates_for_unit_quiz(unit_name)
        
        if not selected_items:
            print(f"Failed to select any templates for unit quiz: {unit_name}")
            return None

        quiz_questions = []
        for item in selected_items:
            template = item["template"]
            marks = item["marks"]
            question_instance = self.question_engine.generate_single_question_instance(template)
            
            if "error" in question_instance:
                print(f"Error generating question instance from template {template.get('id')}: {question_instance['error']}")
                continue

            question_instance["marks"] = marks
            question_instance["unit_name"] = unit_name
            quiz_questions.append(question_instance)
        
        if len(quiz_questions) != 15 and len(selected_items) >= 15 : # Check if generation failed for some
             print(f"Warning: Final unit quiz for '{unit_name}' has {len(quiz_questions)} questions instead of 15 due to generation errors from selected templates.")
        elif len(quiz_questions) < 15: # Check if selection failed
             print(f"Warning: Final unit quiz for '{unit_name}' has {len(quiz_questions)} questions (fewer than 15 selected templates).")
        return quiz_questions

    def score_unit_quiz(self, quiz_questions: List[Dict], student_answers: List[Optional[int]]) -> Dict[str, Any]:
        if not quiz_questions: # Handle empty quiz case
            return {
                "total_score": 0, "max_score": 0, "correct_answers_count": 0,
                "total_questions": 0, "detailed_results": [], "error": "No questions in the quiz to score."
            }
        if len(quiz_questions) != len(student_answers):
            return {"error": "Mismatch between number of questions and answers."}

        total_score = 0
        max_score = 0
        correct_answers_count = 0
        detailed_results = []

        for i, question in enumerate(quiz_questions):
            student_answer_index = student_answers[i]
            is_correct = False
            marks_obtained = 0
            question_marks = question.get("marks", 1) 
            max_score += question_marks

            if student_answer_index is not None and \
               0 <= student_answer_index < len(question.get("options", [])) and \
               student_answer_index == question.get("correct_answer_index"):
                is_correct = True
                correct_answers_count += 1
                total_score += question_marks
                marks_obtained = question_marks
            
            detailed_results.append({
                "question_id": question.get("id"),
                "question_text": question.get("question_text"),
                "options": question.get("options"),
                "student_answer_index": student_answer_index,
                "correct_answer_index": question.get("correct_answer_index"),
                "is_correct": is_correct,
                "marks_obtained": marks_obtained,
                "marks_possible": question_marks
            })
        
        return {
            "total_score": total_score,
            "max_score": max_score, 
            "correct_answers_count": correct_answers_count,
            "total_questions": len(quiz_questions),
            "detailed_results": detailed_results
        }

# --- Example Usage (for testing this file directly) ---
if __name__ == "__main__":
    # (Keep the __main__ block from the previous response for testing)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_backend_dir = os.path.dirname(script_dir) 
    templates_path = os.path.join(project_backend_dir, 'data_initial', 'question_templates.json')
    
    if not os.path.exists(templates_path):
        print(f"CRITICAL ERROR: Templates file not found at {templates_path}")
        exit()
        
    question_eng = QuestionEngine(templates_file_path=templates_path)
    if not question_eng.question_templates:
        print("CRITICAL ERROR: QuestionEngine failed to load templates. Exiting test.")
        exit()

    unit_quiz_gen = UnitQuizGenerator(question_engine=question_eng)
    
    available_units = get_unit_names()
    if not available_units:
        print("No units found in syllabus_config. Cannot test unit quiz generation.")
        exit()

    test_unit_name = available_units[0] 
    print(f"\n--- Generating Quiz for: {test_unit_name} ---")
    
    quiz = unit_quiz_gen.generate_quiz_for_unit(test_unit_name)

    if quiz:
        print(f"Generated {len(quiz)} questions for the unit quiz.")
        actual_total_marks = sum(q.get("marks", 0) for q in quiz)
        print(f"Target marks: 20, Actual calculated marks for generated quiz: {actual_total_marks}")

        one_mark_q_count = sum(1 for q in quiz if q.get("marks") == 1)
        two_mark_q_count = sum(1 for q in quiz if q.get("marks") == 2)
        print(f"1-mark questions: {one_mark_q_count} (Target: 10)")
        print(f"2-mark questions: {two_mark_q_count} (Target: 5)")


        for i, q_instance in enumerate(quiz[:3]): 
            print(f"\nQ{i+1} (ID: {q_instance.get('id')}, Marks: {q_instance.get('marks')}, Type: {q_instance.get('difficulty_type')})")
            print(f"  Text: {q_instance.get('question_text')}")
        
        if len(quiz) > 3: print("...")

        simulated_answers = [random.choice([q.get("correct_answer_index"), random.randint(0,3), None]) if q.get("options") else None for q in quiz]
        
        print(f"\n--- Scoring Simulated Quiz for: {test_unit_name} ---")
        score_result = unit_quiz_gen.score_unit_quiz(quiz, simulated_answers)
        if "error" not in score_result:
            print(f"  Total Score: {score_result['total_score']} / {score_result['max_score']}")
        else:
            print(f"  Error scoring quiz: {score_result['error']}")
    else:
        print(f"Failed to generate quiz for {test_unit_name}.")