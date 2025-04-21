from flask import Blueprint, request, jsonify

from data_services import database
from services.services_middleware import session_required

chat_bp = Blueprint('chat', __name__)


# Route to Fetch Chat
@chat_bp.route("/get-chat")
@session_required
def get_chat():
    user_id = request.session_data.get("user_id", None)
    chat_id = request.values.get("chat_id", None)
    chat = database.get_chat_service(chat_id)

    if chat['data'] is None:
        return jsonify({"data": None, "message": "Chat does not exist!"}), 404
    
    if chat['data']['user_id'] != user_id:
        return jsonify({"data": None, "message": "User is not the owner of this chat"}), 401

    return jsonify(chat), 200

# Route to Create Chat
@chat_bp.route('/new-chat', methods=['GET'])
@session_required
def create_chat():
    user_id = request.session_data.get("user_id")
    if user_id is not None:
        chat_id = database.start_chat_service()
        return jsonify({"data": {"chat_id": chat_id}, "message": "Successfully created new chat"}), 200
    return jsonify({"data": None, "message": "user_id cannot be empty"}), 400
