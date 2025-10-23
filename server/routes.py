from flask import jsonify
from utils import get_user_reports
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

def register_routes(app):

    @app.route('/api/reports', methods=['GET'])
    @jwt_required()
    def get_reports_stub():
        current_user_id = get_jwt_identity()
        try:
            user_reports_list = get_user_reports(current_user_id)
            return jsonify(user_reports_list)
        except Exception as e:
            logger.error(f"Ошибка в get_reports_stub для пользователя {current_user_id}: {str(e)}", exc_info=True)
            return jsonify({"error": "Внутренняя ошибка сервера"}), 500
