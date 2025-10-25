import logging
import hashlib
import base64
from sfera_api import SferaAPI
from models import db, Project, Repository, Commit
from dateutil import parser
from llm_analyzer import analyze_commit_code
from kpi_calculator import calculate_deterministic_kpi, calculate_final_score

logger = logging.getLogger(__name__)

def collect_data_for_target(sfera_username, sfera_password, project_key, repo_name, branch_name, since, until, target_email=None, **kwargs):
    from app import app
    with app.app_context():
        db.session.remove()
        
        logger.info("=== Начало сбора данных ===")
        try:
            api = SferaAPI(username=sfera_username, password=sfera_password)
            
            project = db.session.query(Project).filter_by(key=project_key).first()
            if not project:
                project = Project(key=project_key, name=project_key, description=f"Project {project_key}")
                db.session.add(project)
                db.session.commit()

            repo_unique_str = f"{project_key}/{repo_name}"
            repo_id = int(hashlib.sha1(repo_unique_str.encode('utf-8')).hexdigest(), 16) % (10**9)

            repository = db.session.query(Repository).filter_by(id=repo_id).first()
            if not repository:
                repository = Repository(id=repo_id, name=repo_name, project_key=project_key)
                db.session.add(repository)
                db.session.commit()

            branches_to_scan = [branch_name]
            if branch_name == 'all':
                branches_from_api = api.get_repo_branches(project_key, repo_name)
                branches_to_scan = [b.get('name') for b in branches_from_api if b.get('name')]

            since_dt = parser.isoparse(since)
            until_dt = parser.isoparse(until)
            
            total_commits_found_in_range = 0
            total_newly_saved_commits = 0

            for b_name in branches_to_scan:
                commits_from_api = api.get_repo_commits(project_key, repo_name, branch=b_name, since_dt=since_dt)
                
                if not commits_from_api:
                    continue

                commits_in_range = []
                for commit_data in commits_from_api:
                    commit_date_str = commit_data.get('created_at')
                    if not commit_date_str: continue
                    sha = commit_data.get('hash')
                    if not sha: continue
                    
                    commit_dt = parser.isoparse(commit_date_str)
                    if since_dt <= commit_dt <= until_dt:
                        is_valid = True
                        if target_email and commit_data.get('author', {}).get('email', '').lower() != target_email.lower():
                            is_valid = False
                        
                        if is_valid:
                            commits_in_range.append(commit_data)
                
                total_commits_found_in_range += len(commits_in_range)

                for i, commit_data in enumerate(commits_in_range):
                    sha = commit_data.get('hash')
                    if not sha: continue

                    if db.session.query(Commit).filter_by(sha=sha).first():
                        continue
                        
                    commit_details_response = api.get_commit_details(project_key, repo_name, sha)
                    if not commit_details_response or 'data' not in commit_details_response:
                        continue
                    
                    stats = commit_details_response['data'].get('stats', {})
                    diff_response = api._get(f"projects/{project_key}/repos/{repo_name}/commits/{sha}/diff", params=None)
                    diff_content_base64 = diff_response.get('data', {}).get('content', '')

                    new_commit = Commit(
                        sha=sha,
                        message=commit_data.get('message', ''),
                        author_name=commit_data.get('author', {}).get('name', 'N/A'),
                        author_email=commit_data.get('author', {}).get('email', 'N/A'),
                        commit_date=parser.isoparse(commit_data.get('created_at')),
                        added_lines=stats.get('additions', 0),
                        deleted_lines=stats.get('deletions', 0),
                        repository_id=repository.id,
                        project_key=project_key,
                    )

                    deterministic_kpi = calculate_deterministic_kpi(new_commit.added_lines, new_commit.deleted_lines)
                    new_commit.kpi_difficulty = deterministic_kpi.get('difficulty')
                    new_commit.kpi_quality = deterministic_kpi.get('quality')
                    new_commit.kpi_size = deterministic_kpi.get('size')

                    try:
                        diff_content = base64.b64decode(diff_content_base64).decode('utf-8', errors='ignore')
                        new_commit.commit_content = diff_content
                        
                        analysis_result = analyze_commit_code(diff_content, new_commit.message)
                        
                        if analysis_result and "scores" in analysis_result and analysis_result["scores"]:
                            scores = analysis_result["scores"]
                            new_commit.llm_score_size = scores.get('size')
                            new_commit.llm_score_quality = scores.get('quality')
                            new_commit.llm_score_complexity = scores.get('complexity')
                            new_commit.llm_score_comment = scores.get('comment')
                            new_commit.llm_total_score = scores.get('sum')
                            new_commit.llm_evaluation_text = analysis_result.get("raw_text")
                            
                            new_commit.final_commit_score = calculate_final_score(deterministic_kpi, scores)
                            logger.info(f"Коммит {sha[:7]} успешно проанализирован.")
                    except Exception as e:
                        logger.error(f"Ошибка во время LLM-анализа коммита {sha[:7]}: {e}")

                    db.session.add(new_commit)
                    total_newly_saved_commits += 1
                
                db.session.commit()
                db.session.remove()

            msg = (f"Анализ завершен. Найдено {total_commits_found_in_range} коммитов. "
                   f"Добавлено в базу: {total_newly_saved_commits}.")
            
            logger.info(msg)
            return msg

        except Exception as e:
            logger.error(f"КРИТИЧЕСКАЯ ОШИБКА во время сбора данных: {e}", exc_info=True)
            db.session.rollback()
            return f"Ошибка: {e}"