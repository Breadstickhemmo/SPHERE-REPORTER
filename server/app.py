from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config
from models import db, bcrypt
from logging_config import setup_logging
import os

from routes import register_routes
from auth_routes import register_auth_routes
from admin_routes import register_admin_routes
from sfera_routes import register_sfera_routes
from metrics_routes import register_metrics_routes

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}}, supports_credentials=True)
db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

setup_logging()

if not os.path.exists(Config.REPORT_DIR):
    os.makedirs(Config.REPORT_DIR)
    app.logger.info(f"Создана директория для отчетов: {Config.REPORT_DIR}")

if not os.path.exists(Config.LLM_REPORT_DIR):
    os.makedirs(Config.LLM_REPORT_DIR)
    app.logger.info(f"Создана директория для LLM отчетов: {Config.LLM_REPORT_DIR}")


register_routes(app)
register_auth_routes(app)
register_admin_routes(app)
register_sfera_routes(app)
register_metrics_routes(app)


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)