import requests
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dateutil import parser
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class SferaAPI:
    def __init__(self, username, password, base_url="https://gateway-codemetrics.saas.sferaplatform.ru/app/sourcecode/api/api/v2/"):
        self.base_url = base_url
        self.auth = (username, password)
        self.delay = 0.1
        logger.info("SferaAPI клиент инициализирован успешно.")

    def _get(self, endpoint, params=None):
        try:
            full_url = self.base_url + endpoint
            logger.info(f"Отправка GET запроса к {full_url}")
            if params:
                logger.info(f"Параметры запроса: {params}")
                
            response = requests.get(full_url, auth=self.auth, params=params, verify=False)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Получен ответ от {endpoint}. Статус: {response.status_code}")
            logger.info(f"Структура ответа: {str(data)[:500]}...")
            
            if not isinstance(data, dict):
                logger.error(f"Неожиданный формат ответа от {endpoint}: {type(data)}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка API запроса к {endpoint}: {e}")
            if e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return None
        except ValueError as e:
            logger.error(f"Ошибка парсинга JSON ответа от {endpoint}: {e}")
            return None

    def get_projects(self) -> List[Dict]:
        logger.info("Запрос списка проектов...")
        response_json = self._get("projects")
        return response_json.get('data', []) if response_json else []

    def get_project_repos(self, project_key: str) -> List[Dict]:
        logger.info(f"Запрос списка репозиториев для проекта '{project_key}'...")
        response_json = self._get(f"projects/{project_key}/repos")
        return response_json.get('data', []) if response_json else []

    def get_repo_branches(self, project_key: str, repo_name: str) -> List[Dict]:
        logger.info(f"Запрос веток для {project_key}/{repo_name}...")
        response_json = self._get(f"projects/{project_key}/repos/{repo_name}/branches")
        return response_json.get('data', []) if response_json else []

    def get_repo_commits(self, project_key: str, repo_name: str, branch: Optional[str] = None, since_dt: Optional[datetime] = None) -> List[Dict]:
        logger.info(f"Запрос коммитов для {project_key}/{repo_name} (ветка: {branch or 'default'})")
        
        all_items = []
        cursor = None
        
        while True:
            params = {'limit': 100}
            if cursor:
                params['cursor'] = cursor
            if branch:
                params['rev'] = branch
            
            response_json = self._get(f"projects/{project_key}/repos/{repo_name}/commits", params=params)
            
            if not response_json or 'data' not in response_json:
                logger.warning(f"Ответ API по коммитам для {project_key}/{repo_name} не содержит данных.")
                break
                
            items = response_json.get('data', [])
            if not items:
                logger.info("  -> Получена пустая страница с коммитами, завершаем.")
                break
                
            if items and len(all_items) == 0:
                logger.info("Пример структуры данных коммита:")
                logger.info(str(items[0]))
            
            all_items.extend(items)
            logger.info(f"  -> Загружено {len(items)} коммитов. Всего: {len(all_items)}.")
            
            if since_dt:
                last_commit_in_page = items[-1]
                last_commit_date_str = last_commit_in_page.get('created_at')
                if last_commit_date_str:
                    try:
                        last_commit_dt = parser.isoparse(last_commit_date_str)
                        if last_commit_dt < since_dt:
                            logger.info(f"  -> Достигнуты коммиты старше {since_dt}. Прекращаем загрузку страниц.")
                            break
                    except Exception:
                        pass

            cursor = response_json.get('page', {}).get('next_cursor')
            if not cursor:
                logger.info("  -> Достигнут конец истории коммитов (нет next_cursor).")
                break
                
            time.sleep(self.delay)
            
        logger.info(f"  -> Всего получено {len(all_items)} коммитов от API перед финальной фильтрацией.")
        return all_items

    def get_commit_details(self, project_key: str, repo_name: str, sha: str) -> Optional[Dict]:
        logger.info(f"Запрос деталей коммита {sha[:7]}...")
        response = self._get(f"projects/{project_key}/repos/{repo_name}/commits/{sha}")
        if response:
            if 'data' not in response:
                response['data'] = {}
            if 'stats' not in response['data']:
                response['data']['stats'] = {
                    'additions': 0,
                    'deletions': 0
                }
        return response