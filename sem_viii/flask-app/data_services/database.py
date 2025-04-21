import config

from .cluster_manager import ClusterManager
from .user_collection import UserCollection
from .chat_collection import ChatCollection
from .session_collection import SessionCollection

# Initialize collections
cluster_manager = ClusterManager(config.MONGODB_URI)
user_col = UserCollection(cluster_manager.get_collection(config.DB, config.USER_COLLECTION))
chat_col = ChatCollection(cluster_manager.get_collection(config.DB, config.CHAT_COLLECTION), user_col)
session_col = SessionCollection(cluster_manager.get_collection(config.DB, config.SESSION_COLLECTION), user_col)


# User Sign-In Service
def user_sign_in_service(email, passwd):
    return user_col.retrieve_user(email, passwd)


# User Sign-Up Service
def user_sign_up_service(email, passwd):
    return user_col.create_user({'email': email, 'password': passwd})


# Create Session Service
def create_session_service(user_id):
    session = session_col.create_session(user_id).get('data', None)
    if session is not None:
        del session["_id"], session["user_id"]
        return {"data": {"session": session}, "message": "Session created successfully"}
    return {"data": None, "message": "Failed to create session"}


# Delete Session Service
def delete_session_service(token):
    deleted = session_col.delete_session(token)
    if deleted['data']:
        return {"data": None, "message": "Session deleted successfully"}
    return {"data": None, "message": "Invalid session token"}


# Get User by ID
def get_user_service(user_id):
    return user_col.get_user_by_id(user_id)


# Get Chat by ID
def get_chat_service(chat_id):
    return chat_col.get_chat_by_id(chat_id)


# New Chat
def start_chat_service(user_id):
    return chat_col.start_chat(user_id)


# Check Association
def is_associated(asso_):
    user_id = asso_.get('user_id')
    chat_id = asso_.get('chat_id')
    session_token = asso_.get('session_token')

    if not user_id:
        return {'data': None, 'message': 'User ID is required'}
    if not chat_id and not session_token:
        return {'data': None, 'message': 'At least one of chat ID or session token is required'}

    if chat_id and not chat_col.is_associated(user_id, chat_id):
        return {'data': None, 'message': 'Chat is not associated with the user'}

    return {'data': True, 'message': 'Verification successful'}


# Get Completion
def get_completion(chat_id, completion_time):
    return chat_col.get_completion(chat_id, completion_time)


# Put Completion
def put_completion(user_id, chat_id, completion):
    result = chat_col.put_completion(user_id, chat_id, completion)
    if result:
        return {"data": None, "message": "Completion added successfully"}
    return {"data": None, "message": "Failed to add completion"}


# Add to Completion
def add_to_completion(chat_id, created_at, key, value):
    result = chat_col.add_to_completion(chat_id, created_at, key, value)
    if result:
        return {"data": None, "message": "Data added to completion successfully"}
    return {"data": None, "message": "Failed to add data to completion"}


# User & Chat Verification
def verify(ver_):
    user_id = ver_.get("user_id")
    chat_id = ver_.get("chat_id")

    if user_id and not user_col.get_user_by_id(user_id):
        return {"data": None, "message": "User does not exist"}
    if chat_id and not chat_col.get_chat_by_id(chat_id):
        return {"data": None, "message": "Chat does not exist"}

    return {"data": True, "message": "Verification successful"}
