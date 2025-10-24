from flask import jsonify, request
from flask_jwt_extended import jwt_required
import logging
from models import Project, Repository, Commit
from sfera_api import SferaAPI
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)

def register_routes(app):
    @app.route('/api/data/projects', methods=['GET'])
    @jwt_required()
    def get_projects():
        try:
            projects = Project.query.order_by(Project.key).all()
            return jsonify([
                {"key": p.key, "name": p.name} for p in projects
            ]), 200
        except Exception as e:
            logger.error(f"Ошибка получения проектов из БД: {e}", exc_info=True)
            return jsonify({"error": "Ошибка сервера при получении проектов"}), 500

    @app.route('/api/data/repositories', methods=['GET'])
    @jwt_required()
    def get_repositories():
        project_key = request.args.get('project_key')
        if not project_key:
            return jsonify([]), 200
        try:
            query = Repository.query.filter_by(project_key=project_key).order_by(Repository.name)
            repositories = query.all()
            return jsonify([
                {"id": r.id, "name": r.name} for r in repositories
            ]), 200
        except Exception as e:
            logger.error(f"Ошибка получения репозиториев из БД: {e}", exc_info=True)
            return jsonify({"error": "Ошибка сервера при получении репозиториев"}), 500
            
    @app.route('/api/data/commits', methods=['GET'])
    @jwt_required()
    def get_commits():
        try:
            project_key = request.args.get('project_key')
            repo_name = request.args.get('repo_name')
            author_email = request.args.get('author_email')
            since = request.args.get('since')
            until = request.args.get('until')

            query = Commit.query
            if project_key:
                query = query.filter(Commit.project_key == project_key)
            if repo_name:
                repo = Repository.query.filter_by(name=repo_name, project_key=project_key).first()
                if repo:
                    query = query.filter(Commit.repository_id == repo.id)
            if author_email:
                query = query.filter(Commit.author_email.ilike(f"%{author_email}%"))
            if since:
                query = query.filter(Commit.commit_date >= since)
            if until:
                query = query.filter(Commit.commit_date <= until)

            commits = query.order_by(Commit.commit_date.desc()).limit(100).all()
            return jsonify([c.to_dict() for c in commits]), 200
        except Exception as e:
            logger.error(f"Ошибка получения коммитов по фильтрам: {e}", exc_info=True)
            return jsonify({"error": "Ошибка сервера при получении коммитов"}), 500

    @app.route('/api/data/commits/<string:sha>/details', methods=['GET'])
    @jwt_required()
    def get_commit_details(sha):
        try:
            commit = Commit.query.get(sha)
            if not commit:
                return jsonify({"error": "Коммит не найден"}), 404
            
            return jsonify(commit.to_detailed_dict()), 200
        except Exception as e:
            logger.error(f"Ошибка получения деталей коммита {sha}: {e}", exc_info=True)
            return jsonify({"error": "Внутренняя ошибка сервера"}), 500