import logging

logger = logging.getLogger(__name__)

def calculate_deterministic_kpi(added_lines: int, deleted_lines: int) -> dict:
    lines_count = added_lines + deleted_lines

    difficulty_metrics = lines_count * 0.03
    if difficulty_metrics > 5:
        difficulty_metrics = 5

    quality_metrics = (100 - (difficulty_metrics * 2)) / 20
    if quality_metrics < 1:
        quality_metrics = 1
    
    if lines_count > 80:
        size_metrics = 5
    elif lines_count > 50:
        size_metrics = 4
    elif lines_count > 20:
        size_metrics = 3
    elif lines_count > 10:
        size_metrics = 2
    else:
        size_metrics = 1
        
    return {
        "difficulty": round(difficulty_metrics, 2),
        "quality": round(quality_metrics, 2),
        "size": size_metrics
    }

def calculate_final_score(deterministic_scores: dict, llm_scores: dict) -> float:
    deterministic_sum = sum(deterministic_scores.values())
    llm_sum = llm_scores.get('sum', 0)

    if llm_sum == 0:
        return deterministic_sum

    final_score = (deterministic_sum + llm_sum) / 2
    return round(final_score, 2)