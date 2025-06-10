# EL_Sem4/backend/app/quiz_generator_grand.py
import random
import os
from typing import List, Dict, Any, Optional

from .question_engine import QuestionEngine

class GrandQuizGenerator:
    def __init__(self, question_engine: QuestionEngine):
        self.question_engine = question_engine
        self.all_templates = self.question_engine.get_all_templates()
        if not self.all_templates:
            print("CRITICAL WARNING: No question templates loaded into QuestionEngine. GrandQuizGenerator will not function.")

    def _select_templates_for_grand_quiz(self) -> List[Dict[str, Any]]:
        if not self.all_templates: 
            print("Warning: No question templates loaded for Grand Quiz generation.")
            return []

        # Shuffle ALL templates at the beginning for grand quiz variety
        current_all_templates = list(self.all_templates) # Work with a copy
        random.shuffle(current_all_templates)

        direct_templates = [t for t in current_all_templates if t.get("difficulty_type") == "direct"]
        aptitude_templates = [t for t in current_all_templates if t.get("difficulty_type") == "aptitude"]
        logical_templates = [t for t in current_all_templates if t.get("difficulty_type") == "logical reasoning"]
        
        potential_two_mark_templates = aptitude_templates + logical_templates
        random.shuffle(potential_two_mark_templates) # Shuffle this combined list too

        # ... (rest of the selection logic remains the same, but it will now operate on shuffled lists) ...
        # ... ensure it uses direct_templates and potential_two_mark_templates from above ...
        
        selected_template_objects = [] 
        selected_ids = set()

        # 1. Select 50 direct questions (1 mark)
        count_direct = 0
        for tpl in direct_templates:
            if count_direct < 50 and tpl["id"] not in selected_ids:
                selected_template_objects.append({"template": tpl, "marks": 1})
                selected_ids.add(tpl["id"])
                count_direct += 1
        
        direct_needed = 50 - count_direct
        if direct_needed > 0 and direct_templates:
            available_direct = [t for t in direct_templates if t["id"] not in selected_ids]
            if len(available_direct) < direct_needed:
                available_direct.extend(random.choices(direct_templates, k=direct_needed - len(available_direct)))
            
            chosen_fillers = random.sample(available_direct, min(direct_needed, len(available_direct)))
            for tpl in chosen_fillers:
                 selected_template_objects.append({"template": tpl, "marks": 1})

        # 2. Select 25 aptitude/logical questions (2 marks each)
        count_two_mark = 0
        for tpl in potential_two_mark_templates:
            if count_two_mark < 25 and tpl["id"] not in selected_ids:
                selected_template_objects.append({"template": tpl, "marks": 2})
                selected_ids.add(tpl["id"])
                count_two_mark += 1
        
        two_mark_needed = 25 - count_two_mark
        if two_mark_needed > 0 and potential_two_mark_templates:
            available_two_mark = [t for t in potential_two_mark_templates if t["id"] not in selected_ids]
            if len(available_two_mark) < two_mark_needed:
                available_two_mark.extend(random.choices(potential_two_mark_templates, k=two_mark_needed - len(available_two_mark)))
            
            chosen_fillers = random.sample(available_two_mark, min(two_mark_needed, len(available_two_mark)))
            for tpl in chosen_fillers:
                 selected_template_objects.append({"template": tpl, "marks": 2})


        if len(selected_template_objects) < 75:
            print(f"Warning: Selected {len(selected_template_objects)}/75 templates for Grand Quiz. Quiz will be shorter or have more repeats.")
            # Fallback: Fill with any remaining unique templates from all, then allow repeats
            all_other_templates_pool = [t for t in current_all_templates if t["id"] not in selected_ids]
            
            while len(selected_template_objects) < 75:
                if not all_other_templates_pool:
                    if not current_all_templates: break
                    all_other_templates_pool = current_all_templates # Allow full reuse
                
                if not all_other_templates_pool: break

                tpl = random.choice(all_other_templates_pool)
                current_one_mark_count = sum(1 for item in selected_template_objects if item['marks']==1)
                mark_to_assign = 1 if current_one_mark_count < 50 else 2
                selected_template_objects.append({"template": tpl, "marks": mark_to_assign })
                if tpl in all_other_templates_pool and tpl["id"] in selected_ids:
                     try: all_other_templates_pool.remove(tpl)
                     except ValueError: pass
        
        random.shuffle(selected_template_objects) # Shuffle the final list for presentation order
        return selected_template_objects[:75]


    # generate_grand_quiz and score_grand_quiz methods remain the same as in my immediately previous response.
    # I will include them here for completeness of this file.

    def generate_grand_quiz(self) -> Optional[List[Dict[str, Any]]]:
        selected_items = self._select_templates_for_grand_quiz()
        
        if not selected_items:
            print("Failed to select any templates for Grand Quiz.")
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
            quiz_questions.append(question_instance)

        if len(quiz_questions) != 75 and len(selected_items) >= 75 : 
             print(f"Warning: Grand Quiz has {len(quiz_questions)} questions instead of 75 due to generation errors from selected templates.")
        elif len(quiz_questions) < 75: 
             print(f"Warning: Grand Quiz has {len(quiz_questions)} questions (fewer than 75 selected templates).")
        return quiz_questions

    def score_grand_quiz(self, quiz_questions: List[Dict], student_answers: List[Optional[int]]) -> Dict[str, Any]:
        if not quiz_questions: # Handle empty quiz
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
               0 <= student_answer_index < len(question.get("options",[])) and \
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
        
    grand_quiz_gen = GrandQuizGenerator(question_engine=question_eng)

    print(f"\n--- Generating Grand Quiz ---")
    grand_quiz = grand_quiz_gen.generate_grand_quiz()

    if grand_quiz:
        print(f"Generated {len(grand_quiz)} questions for the Grand Quiz.")
        actual_total_marks_grand = sum(q.get("marks", 0) for q in grand_quiz)
        direct_q_count = sum(1 for q in grand_quiz if q.get("marks") == 1)
        two_mark_q_count = sum(1 for q in grand_quiz if q.get("marks") == 2)
        
        print(f"Target marks: 100, Actual calculated marks for generated quiz: {actual_total_marks_grand}")
        print(f"Number of 1-mark questions: {direct_q_count} (Target: 50)")
        print(f"Number of 2-mark questions: {two_mark_q_count} (Target: 25)")


        simulated_answers_grand = [random.choice([q.get("correct_answer_index"), random.randint(0,3) if q.get("options") and len(q.get("options")) > 0 else 0, None]) for q in grand_quiz]
        
        print(f"\n--- Scoring Simulated Grand Quiz ---")
        score_result_grand = grand_quiz_gen.score_grand_quiz(grand_quiz, simulated_answers_grand)
        if "error" not in score_result_grand:
            print(f"  Total Score: {score_result_grand['total_score']} / {score_result_grand['max_score']}")
        else:
            print(f"  Error scoring quiz: {score_result_grand['error']}")
    else:
        print("Failed to generate Grand Quiz.")