import logging
import hashlib
import time
from datetime import datetime
from sfera_api import SferaAPI
from models import db, Project, Repository, Commit
from dateutil import parser

logger = logging.getLogger(__name__)

def collect_data_for_target(sfera_username, sfera_password, project_key, repo_name, branch_name, since, until, target_email=None, **kwargs):
    from app import app
    with app.app_context():
        db.session.remove()
        
        logger.info("=== Начало сбора данных ===")
        logger.info(f"Параметры:")
        logger.info(f"  - project_key: {project_key}")
        logger.info(f"  - repo_name: {repo_name}")
        logger.info(f"  - branch_name: {branch_name}")
        logger.info(f"  - target_email: {target_email}")
        logger.info(f"  - since: {since}")
        logger.info(f"  - until: {until}")
        commit_count = db.session.query(Commit).count()
        project_count = db.session.query(Project).count()
        repo_count = db.session.query(Repository).count()
        logger.info(f"Текущее состояние БД: проектов - {project_count}, репозиториев - {repo_count}, коммитов - {commit_count}")
        try:
            logger.info(f"НАЧАЛО ЦЕЛЕВОГО СБОРА ДАННЫХ для {project_key}/{repo_name}")
            
            api = SferaAPI(username=sfera_username, password=sfera_password)
            
            project = db.session.query(Project).filter_by(key=project_key).first()
            if not project:
                logger.info(f"Проект '{project_key}' не найден в БД, создаем новый.")
                project = Project(key=project_key, name=project_key, description=f"Project {project_key}")
                db.session.add(project)
                db.session.commit()

            repo_unique_str = f"{project_key}/{repo_name}"
            repo_id = int(hashlib.sha1(repo_unique_str.encode('utf-8')).hexdigest(), 16) % (10**9)

            repository = db.session.query(Repository).filter_by(id=repo_id).first()
            if not repository:
                logger.info(f"Репозиторий '{repo_name}' не найден в БД, создаем новый.")
                repository = Repository(id=repo_id, name=repo_name, project_key=project_key)
                db.session.add(repository)
                db.session.commit()

            branches_to_scan = [branch_name]
            if branch_name == 'all':
                branches_from_api = api.get_repo_branches(project_key, repo_name)
                branches_to_scan = [b.get('name') for b in branches_from_api if b.get('name')]

            logger.info(f"Будет просканировано {len(branches_to_scan)} веток: {branches_to_scan}")

            logger.info(f"Получены даты для парсинга: since='{since}', until='{until}'")
            since_dt = parser.isoparse(since)
            until_dt = parser.isoparse(until)
            
            logger.info(f"Даты успешно распарсены:")
            logger.info(f"  - since_dt: {since_dt} (timestamp: {since_dt.timestamp()})")
            logger.info(f"  - until_dt: {until_dt} (timestamp: {until_dt.timestamp()})")
            
            logger.info(f"Диапазон дат для фильтрации: {since_dt} -> {until_dt}")

            total_commits_found_in_range = 0
            total_newly_saved_commits = 0

            for b_name in branches_to_scan:
                db.session.remove()
                db.session.begin()
                
                logger.info(f"-> Начинаем сбор для ветки: '{b_name}'")
                
                current_commits = db.session.query(Commit).count()
                logger.info(f"  -> Текущее количество коммитов в БД: {current_commits}")
                
                commits_from_api = api.get_repo_commits(project_key, repo_name, branch=b_name, since_dt=since_dt)
                
                if not commits_from_api:
                    logger.warning(f"Коммиты для ветки '{b_name}' не получены от API.")
                    continue

                commits_in_range = []
                for commit_data in commits_from_api:
                    if isinstance(commit_data, dict):
                        logger.info(f"Получены данные коммита: {commit_data}")
                    else:
                        logger.warning(f"Неожиданный формат данных коммита: {type(commit_data)}")
                        continue
                        
                    commit_date_str = commit_data.get('created_at')
                    if not commit_date_str:
                        logger.warning(f"Коммит без даты создания: {commit_data}")
                        continue
                    
                    sha = commit_data.get('hash')
                    if not sha:
                        logger.warning(f"Коммит без hash: {commit_data}")
                        continue
                    
                    logger.info(f"Обработка коммита {sha[:7]} от {commit_data.get('author', {}).get('name')}")
                    
                    commit_dt = parser.isoparse(commit_date_str)
                    logger.info(f"Проверка даты коммита {sha[:7]}: {commit_dt} в диапазоне {since_dt} -> {until_dt}")

                    if since_dt <= commit_dt <= until_dt:
                        logger.info(f"  -> Коммит {sha[:7]} прошел проверку даты")
                        is_valid = True
                        if target_email:
                            author = commit_data.get('author', {})
                            author_email = author.get('email', '').lower()
                            target_email_lower = target_email.lower()
                            
                            logger.info(f"  -> Сравниваем email: '{author_email}' с целевым '{target_email_lower}'")
                            
                            if author_email != target_email_lower:
                                is_valid = False
                                logger.info(f"  -> Пропускаем коммит {sha[:7]} (автор: {author.get('name')}, email: {author_email}) - не соответствует целевому email: {target_email}")
                            else:
                                logger.info(f"  -> [НАЙДЕН] Коммит {sha[:7]} (автор: {author.get('name')}, email: {author_email}) соответствует целевому email")
                        else:
                            logger.info(f"  -> Email фильтрация отключена, пропускаем проверку email")
                        
                        if is_valid:
                            commits_in_range.append(commit_data)
                            logger.info(f"  -> Коммит {sha[:7]} добавлен в список для обработки")
                    else:
                        logger.info(f"  -> Коммит {sha[:7]} не попадает в диапазон дат")
                
                num_found_in_branch = len(commits_in_range)
                total_commits_found_in_range += num_found_in_branch
                target_text = f" для автора {target_email}" if target_email else ""
                logger.info(f"  -> Найдено {num_found_in_branch} коммитов{target_text} в диапазоне. Синхронизируем с БД...")

                newly_saved_in_branch = 0
                for i, commit_data in enumerate(commits_in_range):
                    sha = commit_data.get('hash')
                    if not sha: 
                        logger.warning("Получен коммит без hash, пропускаем")
                        continue

                    existing_commit = db.session.query(Commit).filter_by(sha=sha).first()
                    logger.info(f"  -> Проверка коммита {sha[:7]}: {commit_data.get('message', '')[:50]}...")
                    
                    if existing_commit:
                        logger.info(f"  -> Коммит {sha[:7]} уже существует в БД (автор: {existing_commit.author_name})")
                        continue
                        
                    logger.info(f"  -> Найден новый коммит {sha[:7]}, получаем детали...")

                    commit_details_response = api.get_commit_details(project_key, repo_name, sha)
                    if not commit_details_response or 'data' not in commit_details_response or 'stats' not in commit_details_response['data']:
                        logger.warning(f"Не удалось получить детали для коммита {sha[:7]}. Пропускаем.")
                        continue
                    
                    stats = commit_details_response['data'].get('stats', {})
                    
                    try:
                        new_commit = Commit(
                            sha=sha,
                            message=commit_data.get('message', ''),
                            author_name=commit_data.get('author', {}).get('name', 'N/A'),
                            author_email=commit_data.get('author', {}).get('email', 'N/A'),
                            commit_date=parser.isoparse(commit_data.get('created_at')),
                            added_lines=stats.get('additions', 0),
                            deleted_lines=stats.get('deletions', 0),
                            repository_id=repository.id,
                            project_key=project_key
                        )
                        logger.info(f"Создан объект коммита {sha[:7]} для сохранения в БД")
                    except Exception as e:
                        logger.error(f"Ошибка создания объекта коммита {sha[:7]}: {str(e)}")
                        continue
                    try:
                        if not db.session.query(Commit).filter_by(sha=sha).first():
                            db.session.add(new_commit)
                            try:
                                db.session.commit()
                                newly_saved_in_branch += 1
                                logger.info(f"  -> Успешно сохранен новый коммит: {sha[:7]}")
                            except Exception as e:
                                logger.error(f"  -> Ошибка при commit транзакции для {sha[:7]}: {str(e)}")
                                db.session.rollback()
                        else:
                            logger.warning(f"  -> Коммит {sha[:7]} появился в БД во время обработки, пропускаем")
                    except Exception as e:
                        logger.error(f"  -> Ошибка при сохранении коммита {sha[:7]}: {str(e)}")
                        db.session.rollback()
                
                actual_commits = db.session.query(Commit).count()
                logger.info(f"  -> Статистика ветки '{b_name}':")
                logger.info(f"     * Найдено коммитов в диапазоне: {num_found_in_branch}")
                logger.info(f"     * Сохранено новых коммитов: {newly_saved_in_branch}")
                logger.info(f"     * Всего коммитов в БД: {actual_commits}")
                
                total_newly_saved_commits += newly_saved_in_branch

            if target_email:
                if total_commits_found_in_range > 0:
                    msg = (f"Анализ завершен. Найдено {total_commits_found_in_range} коммитов от автора {target_email}. "
                          f"Из них {total_newly_saved_commits} было добавлено в базу данных.")
                else:
                    msg = f"Анализ завершен. Коммитов от автора {target_email} в указанном диапазоне не найдено."
            else:
                if total_commits_found_in_range > 0:
                    msg = (f"Анализ завершен. Найдено {total_commits_found_in_range} коммитов в диапазоне. "
                          f"Из них {total_newly_saved_commits} было добавлено в базу данных.")
                else:
                    msg = "Анализ завершен. Коммитов в указанном диапазоне не найдено."
            
            logger.info(msg)
            return msg

        except Exception as e:
            logger.error(f"КРИТИЧЕСКАЯ ОШИБКА во время сбора данных: {e}", exc_info=True)
            db.session.rollback()
            return f"Ошибка: {e}"