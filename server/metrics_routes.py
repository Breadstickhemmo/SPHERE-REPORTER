from flask import jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, distinct
from collections import defaultdict
from datetime import datetime, timedelta

from models import db, Commit

def register_metrics_routes(app):
    @app.route('/api/metrics/dashboard_stats', methods=['GET'])
    @jwt_required()
    def get_dashboard_stats():
        total_commits = db.session.query(func.count(Commit.sha)).scalar()
        
        if total_commits == 0:
            return jsonify({
                "summary": {
                    "total_commits": 0,
                    "total_lines_changed": 0,
                    "active_contributors": 0,
                    "last_commit_date": None,
                },
                "top_contributors": [],
                "commit_activity": {"labels": [], "data": []}
            }), 200

        total_lines_added = db.session.query(func.sum(Commit.added_lines)).scalar()
        total_lines_deleted = db.session.query(func.sum(Commit.deleted_lines)).scalar()
        active_contributors = db.session.query(func.count(distinct(Commit.author_name))).scalar()
        
        last_commit_date = db.session.query(func.max(Commit.commit_date)).scalar()

        summary = {
            "total_commits": total_commits or 0,
            "total_lines_changed": int(total_lines_added + total_lines_deleted) if total_lines_added else 0,
            "active_contributors": active_contributors or 0,
            "last_commit_date": last_commit_date.isoformat() if last_commit_date else None,
        }

        top_contributors_query = db.session.query(
            Commit.author_name,
            func.avg(Commit.final_commit_score).label('avg_kpi'),
            func.count(Commit.sha).label('commit_count')
        ).filter(Commit.final_commit_score.isnot(None))\
         .group_by(Commit.author_name)\
         .order_by(func.avg(Commit.final_commit_score).desc())\
         .limit(5).all()
        
        max_possible_score = 17.5
        top_contributors = [
            {
                "author": author,
                "average_kpi": int((avg_kpi / max_possible_score) * 100) if avg_kpi else 0,
                "commits": count
            } for author, avg_kpi, count in top_contributors_query
        ]
        
        first_commit_date = db.session.query(func.min(Commit.commit_date)).scalar()
        if first_commit_date:
            commits_by_day = db.session.query(
                func.date(Commit.commit_date),
                func.count(Commit.sha)
            ).group_by(func.date(Commit.commit_date)).order_by(func.date(Commit.commit_date)).all()
            
            activity_data = {dt.strftime('%Y-%m-%d'): count for dt, count in commits_by_day}
            
            filled_activity = defaultdict(int)
            current_date = first_commit_date.date()
            end_date = last_commit_date.date()
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                filled_activity[date_str] = activity_data.get(date_str, 0)
                current_date += timedelta(days=1)
            
            sorted_activity = sorted(filled_activity.items())
            
            commit_activity = {
                "labels": [item[0] for item in sorted_activity],
                "data": [item[1] for item in sorted_activity]
            }
        else:
            commit_activity = {"labels": [], "data": []}
            
        return jsonify({
            "summary": summary,
            "top_contributors": top_contributors,
            "commit_activity": commit_activity
        }), 200