import bson
import secrets
from datetime import datetime, timedelta
from .collection import _Collection


class SessionCollection(_Collection):
    def __init__(self, collection, user_col):
        super().__init__(collection)
        self.user_col = user_col


    # Function to create a new session
    def create_session(self, user_id):
        print(user_id)
        user = self.user_col.find_document({'_id': bson.ObjectId(user_id)})
        if user is None:
            return {'data': None, 'message': "User does not exist"}
        existing_sessions = self.find_documents({"user_id": user_id})
        for session in existing_sessions:
            self.remove_document({"_id": session["_id"]})
            
        session_token = secrets.token_hex(32)
        expiration_time = datetime.now() + timedelta(hours=24)  # Session expires in 24 hours

        session = {
            "user_id": user_id,
            "session_token": session_token,
            "created_at": str(datetime.now()),
            "expires_at": str(expiration_time),
        }

        insert_result = self.insert_document(session)
        session_id = str(insert_result.inserted_id)
        session['_id'] = session_id

        # Update user document with new session ID
        self.user_col.update_document({'_id': bson.ObjectId(user_id)}, {"$set": {"session_id": session_id}}) 

        return {'data': session, 'message': "Session created successfully"}


    # Function to validate a session
    def validate_session(self, session_token):
        session = self.find_document({"session_token": session_token})
        if session is None:
            return {'data': None, 'message': "Invalid session token"}
        
        expiration_time = datetime.strptime(session["expires_at"], "%Y-%m-%d %H:%M:%S.%f")
        if datetime.now() >= expiration_time:
            self.remove_document({"_id": session["_id"]})
            return {'data': None, 'message': "Session has expired"}

        return {'data': session, 'message': "Session is valid"}


    # Function to delete a session
    def delete_session(self, session_token):
        session = self.find_document({"session_token": session_token})
        if not self._check_document_exists(session, "Session"):
            return {'data': None, 'message': "Invalid session token"}

        self.remove_document({"_id": session["_id"]})
        return {'data': True, 'message': "Session deleted successfully"}


    # Function to retrieve all sessions for a user
    def get_sessions_for_user(self, user_id):
        sessions = self.find_documents({"user_id": user_id})
        if not sessions:
            return {'data': [], 'message': "No active sessions found"}

        session_list = [
            {
                "session_id": str(session["_id"]),
                "session_token": session["session_token"],
                "created_at": session["created_at"],
                "expires_at": session["expires_at"],
            }
            for session in sessions
        ]
        return {'data': session_list, 'message': "Sessions retrieved successfully"}
