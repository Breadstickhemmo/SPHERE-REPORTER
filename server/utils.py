import logging

logger = logging.getLogger(__name__)

def get_user_reports(user_id: str) -> list:
    
    logger.info(f"Заглушка: Запрос метрик для пользователя {user_id}")
    return []