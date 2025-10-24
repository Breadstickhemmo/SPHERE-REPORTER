from flask import jsonify, request
from flask_jwt_extended import jwt_required
import threading
import logging
from data_collector import collect_data_for_target

logger = logging.getLogger(__name__)

data_collection_status = {"is_running": False, "last_run": None, "message": "Процесс не запускался"}

def run_collection_wrapper(params):
    data_collection_status["is_running"] = True
    data_collection_status["message"] = "Процесс сбора данных запущен..."
    logger.info("Процесс сбора данных запущен с параметрами: %s", params)
    try:
        result_message = collect_data_for_target(**params)
        data_collection_status["last_run"] = "успешно"
        data_collection_status["message"] = result_message
    except Exception as e:
        logger.error(f"Процесс сбора данных завершился с ошибкой: {e}", exc_info=True)
        data_collection_status["last_run"] = "с ошибкой"
        data_collection_status["message"] = f"Ошибка: {e}"
    finally:
        data_collection_status["is_running"] = False
        logger.info("Процесс сбора данных завершен.")

def register_admin_routes(app):
    @app.route('/api/admin/start-collection', methods=['POST'])
    @jwt_required()
    def start_collection():
        if data_collection_status["is_running"]:
            return jsonify({"message": "Процесс сбора данных уже запущен."}), 409
        
        data = request.get_json()
        if not data or 'sfera_username' not in data or 'sfera_password' not in data:
            return jsonify({"message": "Не предоставлены учетные данные Sfera"}), 400
        
        thread = threading.Thread(target=run_collection_wrapper, args=(data,), name="data_collector_thread")
        thread.daemon = True
        thread.start()
        
        return jsonify({"message": "Процесс анализа данных запущен в фоновом режиме."}), 202

    @app.route('/api/admin/collection-status', methods=['GET'])
    @jwt_required()
    def get_collection_status():
        return jsonify(data_collection_status), 200