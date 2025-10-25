from flask import jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, distinct
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import re
import numpy as np

from models import db, Commit, Repository

def register_metrics_routes(app):

    def apply_filters_to_query(query):
        project_key = request.args.get('project_key')
        repo_name = request.args.get('repo_name')
        author_email = request.args.get('author_email')
        since = request.args.get('since')
        until = request.args.get('until')

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
        
        return query

    @app.route('/api/metrics/dashboard_stats', methods=['GET'])
    @jwt_required()
    def get_dashboard_stats():
        base_query = db.session.query(Commit)
        filtered_query = apply_filters_to_query(base_query)

        total_commits = filtered_query.count()
        
        if total_commits == 0:
            return jsonify({
                "summary": {"total_commits": 0, "total_lines_changed": 0, "active_contributors": 0, "last_commit_date": None},
                "top_contributors": [],
                "commit_activity": {"labels": [], "data": []}
            }), 200

        summary_data = filtered_query.with_entities(
            func.sum(Commit.added_lines + Commit.deleted_lines),
            func.count(distinct(Commit.author_name)),
            func.max(Commit.commit_date)
        ).first()

        summary = {
            "total_commits": total_commits,
            "total_lines_changed": int(summary_data[0]) if summary_data[0] else 0,
            "active_contributors": summary_data[1] or 0,
            "last_commit_date": summary_data[2].isoformat() if summary_data[2] else None,
        }
        
        # Получаем всех контрибьюторов для выпадающего списка
        all_contributors_query = filtered_query.with_entities(
            Commit.author_name, Commit.author_email
        ).distinct().all()
        
        top_contributors_query = filtered_query.with_entities(
            Commit.author_name,
            func.avg(Commit.final_commit_score).label('avg_kpi'),
            func.count(Commit.sha).label('commit_count')
        ).filter(Commit.final_commit_score.isnot(None))\
         .group_by(Commit.author_name)\
         .order_by(func.avg(Commit.final_commit_score).desc())\
         .limit(5).all()
        
        max_possible_score = 17.5
        top_contributors = [
            {"author": author, "average_kpi": int((avg_kpi / max_possible_score) * 100) if avg_kpi else 0, "commits": count}
            for author, avg_kpi, count in top_contributors_query
        ]
        
        return jsonify({
            "summary": summary, 
            "top_contributors": top_contributors,
            "all_contributors": [{"name": name, "email": email} for name, email in all_contributors_query]
        }), 200

    @app.route('/api/metrics/user_summary', methods=['GET'])
    @jwt_required()
    def get_user_summary():
        author_email = request.args.get('author_email')
        if not author_email:
            return jsonify({"error": "author_email is required"}), 400

        base_query = db.session.query(Commit).filter(Commit.author_email.ilike(f"%{author_email}%"))
        query_with_filters = apply_filters_to_query(base_query)
        
        user_commits = query_with_filters.all()

        if not user_commits:
            return jsonify({"summary": {"total_commits": 0}, "recommendation": "Нет данных для анализа."}), 200

        # Сводка KPI
        scores = [c.final_commit_score for c in user_commits if c.final_commit_score is not None]
        avg_score = np.mean(scores) if scores else 0
        max_possible_score = 17.5
        avg_kpi_100 = int((avg_score / max_possible_score) * 100)
        
        summary = {
            "total_commits": len(user_commits),
            "average_kpi": avg_kpi_100
        }

        # Генерация рекомендации
        avg_llm_scores = {
            "качество": np.mean([c.llm_score_quality for c in user_commits if c.llm_score_quality is not None]) if any(c.llm_score_quality for c in user_commits) else 5,
            "сложность": np.mean([c.llm_score_complexity for c in user_commits if c.llm_score_complexity is not None]) if any(c.llm_score_complexity for c in user_commits) else 5,
            "комментарий": np.mean([c.llm_score_comment for c in user_commits if c.llm_score_comment is not None]) if any(c.llm_score_comment for c in user_commits) else 5,
        }
        
        lowest_category = min(avg_llm_scores, key=avg_llm_scores.get)
        
        recommendations_map = {
            "качество": "Основная зона роста - качество кода. Старайтесь следовать принципам SOLID, избегать дублирования и писать более чистые функции.",
            "сложность": "Рекомендуется обратить внимание на сложность реализуемых задач. Возможно, стоит браться за более комплексные фичи для профессионального роста.",
            "комментарий": "Ваша ключевая точка роста - написание комментариев к коммитам. Старайтесь делать их более информативными, описывая суть изменений и ссылаясь на номер задачи."
        }
        recommendation = f"Анализ коммитов за выбранный период показывает, что ваш средний KPI составляет {avg_kpi_100}/100. \n\n{recommendations_map.get(lowest_category, 'Продолжайте в том же духе!')}"

        return jsonify({"summary": summary, "recommendation": recommendation}), 200