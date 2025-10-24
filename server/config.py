import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SFERA_USERNAME = os.getenv('SFERA_USERNAME')
    SFERA_PASSWORD = os.getenv('SFERA_PASSWORD')
    
    # --- НОВАЯ ПЕРЕМЕННАЯ ---
    GIGACHAT_CREDENTIALS = os.getenv('GIGACHAT_CREDENTIALS')

    REPORT_DIR = os.path.abspath("reports")
    LLM_REPORT_DIR = os.path.abspath("llm_reports")
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.html', '.css',
        '.java', '.cpp', '.c', '.cs', '.go', '.php',
        '.rb', '.swift', '.kt', '.scala'
    }
    CORS_ORIGINS = ["http://localhost:3000"]
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60