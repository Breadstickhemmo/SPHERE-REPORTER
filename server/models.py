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

    def __repr__(self):
        return f'<User {self.username}>'

class Project(db.Model):
    __tablename__ = 'projects'
    key = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    repositories = db.relationship(
        'Repository', 
        foreign_keys='Repository.project_key',
        backref='project', 
        lazy=True, 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<Project {self.key}>'

class Repository(db.Model):
    __tablename__ = 'repositories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    project_key = db.Column(db.String(255), db.ForeignKey('projects.key'), nullable=False)
    
    commits = db.relationship('Commit', backref='repository', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'project_key': self.project_key}

class Commit(db.Model):
    __tablename__ = 'commits'
    sha = db.Column(db.String(40), primary_key=True)
    message = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(255), nullable=False)
    author_email = db.Column(db.String(255), nullable=True)
    commit_date = db.Column(db.DateTime(timezone=True), nullable=False)
    commit_content=db.Column(db.String, nullable=True)
    added_lines = db.Column(db.Integer, default=0)
    deleted_lines = db.Column(db.Integer, default=0)
    difficult_metrics = db.Column(db.Float, default=0.0)
    quality_metrics = db.Column(db.Float, default=0.0)
    size_metrics = db.Column(db.Integer, default=0)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    project_key = db.Column(db.String, db.ForeignKey('projects.key'), nullable=True)

    def to_dict(self):
        return {
            'sha': self.sha,
            'message': self.message,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'commit_date': self.commit_date.isoformat(),
            'added_lines': self.added_lines,
            'deleted_lines': self.deleted_lines,
            'repository_id': self.repository_id
        }