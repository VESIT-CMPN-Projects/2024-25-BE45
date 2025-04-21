import bson
from datetime import datetime
from .collection import _Collection
from bcrypt import hashpw, checkpw, gensalt


class UserCollection(_Collection):
    def __init__(self, collection):
        super().__init__(collection)


    # Function to create a new user
    def create_user(self, user):
        if self.find_document({'email': user['email']}) is not None:
            return {'data': None, 'message': "User with this email already exists"}

        user_doc = {
            "email": user["email"],
            "password": hashpw(user["password"].encode("utf-8"), gensalt()),
            "chats": [],
            "joined_at": str(datetime.now())
        }

        insert_result = self.insert_document(user_doc)
        return {'data': {'user_id' : str(insert_result.inserted_id)}, 'message': "User created successfully"}


    # Function to retrieve a user
    def retrieve_user(self, email, passwd):
        user = self.find_document({'email': email})
        if user is not None:
            if checkpw(passwd.encode("utf-8"), user["password"]):
                del user["password"]
                user["_id"] = str(user["_id"])
                return {'data': user, 'message': "User retrieved successfully"}
            return {'data': None, 'message': "Invalid credentials"}
        return {'data': None, 'message': "User does not exist"}


    # Function to update chats for a user
    def update_user_chats(self, user_id, chat_id, action="add"):
        user = self.find_document({'_id': bson.ObjectId(user_id)})
        if not user is not None:
            return {'data': None, 'message': "User does not exist"}

        if action == "add" and chat_id not in user["chats"]:
            user["chats"].append(chat_id)
        elif action == "remove" and chat_id in user["chats"]:
            user["chats"].remove(chat_id)
        else:
            return {'data': None, 'message': "Invalid action or chat not found"}

        result = self.update_document({'_id': bson.ObjectId(user_id)}, {'$set': {'chats': user["chats"]}})
        return {'data': result.modified_count > 0, 'message': "User chats updated successfully"}


    # Function to Retrieve User by ID
    def get_user_by_id(self, user_id):
        user = self.find_document({'_id': bson.ObjectId(user_id)})
        if user is not None:
            del user["password"]
            del user["_id"]
            return {'data': user, 'message': "User retrieved successfully"}
        return {'data': None, 'message': "User does not exist"}
    

    # Function to Delete User and all their associated Chats
    def delete_user(self, user_id, chat_col):
        user = self.find_document({'_id': bson.ObjectId(user_id)})
        if not self._check_document_exists(user, "User"):
            return {'data': None, 'message': "User does not exist"}
        
        for chat_id in user["chats"]:
            chat_col.del_chat(user_id, chat_id)

        delete_result = self.remove_document({'_id': bson.ObjectId(user_id)})
        if delete_result.deleted_count > 0:
            return {'data': True, 'message': "User deleted successfully"}
        return {'data': None, 'message': "Failed to delete user"}
    