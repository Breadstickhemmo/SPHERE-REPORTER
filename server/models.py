from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Project(db.Model):
    __tablename__ = 'projects'
    key = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    repositories = db.relationship('Repository', backref='project', lazy=True)

class Repository(db.Model):
    __tablename__ = 'repositories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    project_key = db.Column(db.String(255), db.ForeignKey('projects.key'), nullable=False)
    commits = db.relationship('Commit', backref='repository', lazy=True)

class Commit(db.Model):
    __tablename__ = 'commits'
    sha = db.Column(db.String(40), primary_key=True)
    message = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(255), nullable=False)
    author_email = db.Column(db.String(255), nullable=True)
    commit_date = db.Column(db.DateTime(timezone=True), nullable=False)
    commit_content = db.Column(db.Text, nullable=True)
    added_lines = db.Column(db.Integer, default=0)
    deleted_lines = db.Column(db.Integer, default=0)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    project_key = db.Column(db.String, db.ForeignKey('projects.key'), nullable=True)

    kpi_difficulty = db.Column(db.Float, nullable=True)
    kpi_quality = db.Column(db.Float, nullable=True)
    kpi_size = db.Column(db.Integer, nullable=True)

    llm_score_size = db.Column(db.Integer, nullable=True)
    llm_score_quality = db.Column(db.Integer, nullable=True)
    llm_score_complexity = db.Column(db.Integer, nullable=True)
    llm_score_comment = db.Column(db.Integer, nullable=True)
    llm_total_score = db.Column(db.Integer, nullable=True)
    llm_evaluation_text = db.Column(db.Text, nullable=True)
    
    final_commit_score = db.Column(db.Float, nullable=True)

    def to_dict(self):
        max_possible_score = 17.5 
        score_100 = None
        if self.final_commit_score is not None:
            score_100 = int((self.final_commit_score / max_possible_score) * 100)

        return {
            'sha': self.sha,
            'message': self.message.splitlines()[0],
            'author_name': self.author_name,
            'commit_date': self.commit_date.isoformat(),
            'total_score_100': score_100
        }

    def to_detailed_dict(self):
        base_dict = self.to_dict()
        base_dict.update({
            'llm_scores': {
                'size': self.llm_score_size,
                'quality': self.llm_score_quality,
                'complexity': self.llm_score_complexity,
                'comment': self.llm_score_comment
            },
            'llm_recommendations': self.llm_evaluation_text
        })
        return base_dict