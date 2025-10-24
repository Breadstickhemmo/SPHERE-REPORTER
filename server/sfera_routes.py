from flask import jsonify, request
from flask_jwt_extended import jwt_required
import logging
from sfera_api import SferaAPI
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)

def register_sfera_routes(app):

    def get_credentials(data):
        sfera_username = data.get('sfera_username')
        sfera_password = data.get('sfera_password')
        if not sfera_username or not sfera_password:
            raise ValueError("Не предоставлены учетные данные для Sfera API")
        return sfera_username, sfera_password

    @app.route('/api/sfera/projects', methods=['POST'])
    @jwt_required()
    def get_sfera_projects():
        try:
            sfera_username, sfera_password = get_credentials(request.get_json())
            api = SferaAPI(username=sfera_username, password=sfera_password)
            projects = api.get_projects()
            return jsonify([{"key": p.get("name"), "name": p.get("name")} for p in projects if p.get("name")]), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except HTTPError as e:
            if e.response.status_code == 401:
                return jsonify({"error": "Неверный логин или пароль для Sfera API"}), 401
            return jsonify({"error": "Ошибка при запросе к Sfera API"}), 500
        except Exception as e:
            logger.error(f"Критическая ошибка при запросе проектов из Sfera: {e}", exc_info=True)
            return jsonify({"error": "Внутренняя ошибка сервера"}), 500

    @app.route('/api/sfera/repositories', methods=['POST'])
    @jwt_required()
    def get_sfera_repositories():
        try:
            data = request.get_json()
            sfera_username, sfera_password = get_credentials(data)
            project_key = data.get('project_key')
            if not project_key:
                return jsonify({"error": "Не указан project_key"}), 400

            api = SferaAPI(username=sfera_username, password=sfera_password)
            repos = api.get_project_repos(project_key)
            return jsonify([{"name": r.get("name")} for r in repos if r.get("name")]), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except HTTPError as e:
            if e.response.status_code == 401:
                return jsonify({"error": "Неверный логин или пароль для Sfera API"}), 401
            return jsonify({"error": f"Ошибка при запросе репозиториев: {e.response.text}"}), 500
        except Exception as e:
            logger.error(f"Критическая ошибка при запросе репозиториев из Sfera: {e}", exc_info=True)
            return jsonify({"error": "Внутренняя ошибка сервера"}), 500

    @app.route('/api/sfera/branches', methods=['POST'])
    @jwt_required()
    def get_sfera_branches():
        try:
            data = request.get_json()
            sfera_username, sfera_password = get_credentials(data)
            project_key = data.get('project_key')
            repo_name = data.get('repo_name')
            if not project_key or not repo_name:
                return jsonify({"error": "Не указаны project_key и repo_name"}), 400

            api = SferaAPI(username=sfera_username, password=sfera_password)
            branches = api.get_repo_branches(project_key, repo_name)
            return jsonify([{"name": b.get("name")} for b in branches if b.get("name")]), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except HTTPError as e:
            if e.response.status_code == 401:
                return jsonify({"error": "Неверный логин или пароль для Sfera API"}), 401
            if e.response.status_code == 404:
                return jsonify([]), 200
            return jsonify({"error": f"Ошибка при запросе веток: {e.response.text}"}), 500
        except Exception as e:
            logger.error(f"Критическая ошибка при запросе веток из Sfera: {e}", exc_info=True)
            return jsonify({"error": "Внутренняя ошибка сервера"}), 500