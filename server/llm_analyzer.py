import logging
import re
from gigachat import GigaChat
from config import Config

logger = logging.getLogger(__name__)

giga = None
if Config.GIGACHAT_CREDENTIALS:
    try:
        giga = GigaChat(
            credentials=Config.GIGACHAT_CREDENTIALS,
            verify_ssl_certs=False,
            model="GigaChat-Max"
        )
        logger.info("GigaChat клиент успешно инициализирован.")
    except Exception as e:
        giga = None
        logger.error(f"Не удалось инициализировать GigaChat: {e}")
else:
    logger.warning("GIGACHAT_CREDENTIALS не найден в .env. LLM-анализатор будет отключен.")


def parse_evaluation(text: str) -> dict:
    scores = {}
    patterns = {
        'size': r"Размер:\s*(\d)",
        'quality': r"Качество:\s*(\d)",
        'complexity': r"Сложность:\s*(\d)",
        'comment': r"Комментарий:\s*(\d)",
        'sum': r"Сумма:\s*(\d+)"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            scores[key] = int(match.group(1))
    return scores

def analyze_commit_code(diff_content: str) -> dict:
    if not giga:
        logger.warning("GigaChat клиент не инициализирован. Анализ пропускается.")
        return {}

    if len(diff_content) > 4000:
        diff_content = diff_content[:4000] + "\n... [содержимое обрезано]"

    prompt = f"""Ты строгий тимлид, который точен в оценках. Не усредняй баллы и следуй критериям буквально. Оцени следующий коммит СТРОГО по указанным критериям:

ПРАВИЛА ОЦЕНКИ:
1. РАЗМЕР - подсчитай общее количество добавленных и удаленных строк в коммите:
   1 балл - менее 10 строк изменений
   2 балла - 10-20 строк изменений
   3 балла - 20-50 строк изменений  
   4 балла - 50-80 строк изменений
   5 баллов - более 80 строк изменений

2. КАЧЕСТВО - проанализируй содержание изменений:
   1-2 балла - изменения явно вносят новые баги или ухудшают код
   3 балла - изменения нейтральны, но могли быть реализованы лучше
   4-5 баллов - изменения улучшают код, багов не вносят

3. СЛОЖНОСТЬ - оцени сложность реализации:
    1 балл - тривиальные изменения (опечатки, переименования)
    2 балла - простые изменения (корректировка формата, мелкие правки)
    3 балла - изменения средней сложности (рефакторинг, добавление фич)
    4-5 баллов - сложные изменения (архитектурные правки, сложная логика)
    
4. КОММЕНТАРИЙ - оцени наличие и структуру сообщения коммита:
    1 балл - сообщение плохо описывает происходящее в коде или его нет
    2 балла - минимальное описание
    3 балла - сообщение нормальное
    4 балла - сообщение объёмное, но не конкретное
    5 балл - сообщение полностью отражает все изменения в коде

ВАЖНО: 
- Оценивай КАЖДЫЙ критерий НЕЗАВИСИМО
- Подсчитывай РЕАЛЬНОЕ количество строк в коммите
- Не усредняй оценки между критериями
- Оценивай строго согласно метрикам

КОММИТ ДЛЯ АНАЛИЗА:
{diff_content}

Ответ СТРОГО в формате и ТОЛЬКО согласно формату:
Размер: X
Качество: Y
Сложность: Z
Комментарий: U
Сумма: (сумма всех предыдущих)"""

    try:
        response = giga.chat(prompt)
        evaluation_text = response.choices[0].message.content
        logger.info(f"GigaChat вернул оценку:\n{evaluation_text}")
        
        parsed_scores = parse_evaluation(evaluation_text)
        
        return {
            "scores": parsed_scores,
            "raw_text": evaluation_text
        }
    except Exception as e:
        logger.error(f"Ошибка при взаимодействии с GigaChat: {e}", exc_info=True)
        return {}