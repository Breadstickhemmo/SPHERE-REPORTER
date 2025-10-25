from flask import jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, distinct
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import re

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
        
        first_commit_date = filtered_query.with_entities(func.min(Commit.commit_date)).scalar()
        if first_commit_date:
            commits_by_day_query = filtered_query.with_entities(
                func.date(Commit.commit_date),
                func.count(Commit.sha)
            ).group_by(func.date(Commit.commit_date)).order_by(func.date(Commit.commit_date)).all()
            
            activity_data = {dt.strftime('%Y-%m-%d'): count for dt, count in commits_by_day_query}
            filled_activity = defaultdict(int)
            current_date = first_commit_date.date()
            end_date = summary.get("last_commit_date")
            end_date = datetime.fromisoformat(end_date).date() if end_date else datetime.utcnow().date()
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                filled_activity[date_str] = activity_data.get(date_str, 0)
                current_date += timedelta(days=1)
            
            sorted_activity = sorted(filled_activity.items())
            commit_activity = {"labels": [item[0] for item in sorted_activity], "data": [item[1] for item in sorted_activity]}
        else:
            commit_activity = {"labels": [], "data": []}
            
        return jsonify({"summary": summary, "top_contributors": top_contributors, "commit_activity": commit_activity}), 200

    @app.route('/api/metrics/hotspots', methods=['GET'])
    @jwt_required()
    def get_hotspots():
        base_query = db.session.query(Commit).filter(Commit.commit_content.isnot(None))
        filtered_query = apply_filters_to_query(base_query)
        commits = filtered_query.all()
        
        file_counts = Counter()
        file_pattern = re.compile(r'^\+\+\+ b/(.*)$', re.MULTILINE)

        for commit in commits:
            try:
                changed_files = file_pattern.findall(commit.commit_content)
                file_counts.update(changed_files)
            except Exception:
                continue
        
        hotspots = [{"file": file, "changes": count} for file, count in file_counts.most_common(10)]
        return jsonify(hotspots), 200

    @app.route('/api/metrics/temporal_patterns', methods=['GET'])
    @jwt_required()
    def get_temporal_patterns():
        base_query = db.session.query(Commit)
        filtered_query = apply_filters_to_query(base_query)

        results = filtered_query.with_entities(
            func.extract('isodow', Commit.commit_date).label('day_of_week'),
            func.extract('hour', Commit.commit_date).label('hour_of_day'),
            func.count(Commit.sha).label('commit_count')
        ).group_by('day_of_week', 'hour_of_day').all()

        day_map = {1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб', 7: 'Вс'}

        patterns = [
            {"day": day_map.get(row.day_of_week), "hour": int(row.hour_of_day), "commits": row.commit_count}
            for row in results if row.day_of_week in day_map
        ]
        return jsonify(patterns), 200