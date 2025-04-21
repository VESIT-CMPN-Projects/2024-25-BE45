import bson
from datetime import datetime
from .collection import _Collection


class ChatCollection(_Collection):
    def __init__(self, collection, user_col):
        super().__init__(collection)
        self.user_col = user_col


    # Function to Create Chat
    def start_chat(self, user_id):
        user = self.user_col.find_document({'_id': bson.ObjectId(user_id)})
        if user is not None:
            doc = {"user_id": user_id, "created_at": str(datetime.now()), "completions": {}}
            insert_result = self.insert_document(doc)
            chat_id = str(insert_result.inserted_id)
            self.user_col.update_user_chats(user_id, chat_id)
            return {'data': chat_id, 'message': "Chat started successfully"}
        return {'data': None, 'message': "User does not exist"}


    # Function to Delete Chat
    def del_chat(self, user_id, chat_id):
        chat = self.find_document({'_id': bson.ObjectId(chat_id)})
        if chat is not None:
            self.remove_document({'_id': bson.ObjectId(chat_id)})
            self.user_col.update_user_chats(user_id, chat_id, action="remove")
            return {'data': chat_id, 'message': "Chat deleted successfully"}
        return {'data': None, 'message': "Chat does not exist"}


    # Function to Put Completion in Chat
    def put_completion(self, user_id, chat_id, completion):
        user = self.user_col.find_document({'_id': bson.ObjectId(user_id)})
        if user is not None:
            if chat_id in user["chats"]:
                chat = self.find_document({'_id': bson.ObjectId(chat_id)})
                if chat is not None:
                    completion_key = completion["created_at"]
                    del completion["created_at"]
                    chat["completions"].update({completion_key: completion})
                    chat_bson_id = chat.pop('_id')
                    result = self.update_document({'_id': chat_bson_id}, {'$set': chat})
                    return {'data': (result.matched_count > 0, result.modified_count > 0), 'message': "Completion added"}
            return {'data': None, 'message': "Chat is not associated with the User"}
        return {'data': None, 'message': "User does not exist"}


    # Function to Get Completion by Completion Time
    def get_completion(self, chat_id, completion_time):
        chat = self.find_document({'_id': bson.ObjectId(chat_id)})
        if chat is not None:
            if completion_time in chat["completions"]:
                return {'data': chat["completions"][completion_time], 'message': 'Successfully fetched'}
            return {'data': None, 'message': 'Invalid Completion Time'}
        return {'data': None, 'message': "Chat does not exist"}


    # Function to Add to key-value pair to Completion
    def add_to_completion(self, chat_id, completion_time, key, value):
        chat = self.find_document({'_id': bson.ObjectId(chat_id)})
        if chat is not None:
            if completion_time in chat["completions"]:
                update_result = self.update_document(
                    {"_id": bson.ObjectId(chat_id)},
                    {"$set": {f"completions.{completion_time}.{key}": value}}
                )
                return {'data': update_result.modified_count > 0, 'message': "Completion updated"}
            return {'data': None, 'message': 'Invalid Completion Time'}
        return {'data': None, 'message': "Chat does not exist"}


    # Function to Add to key-value pair to Completion
    def get_chats_for_user(self, user_id):
        chats = self.find_documents({'user_id': user_id})
        chat_ids = [str(chat['_id']) for chat in chats]
        return {'data': chat_ids, 'message': "Successfully retrieved all chats"}


    # Function to check if User is associated with Chat
    def is_associated(self, user_id, chat_id):
        chat = self.find_document({'_id': bson.ObjectId(chat_id)})
        if chat is None:
            return {'data': False, 'message': "Chat does not exist"}
        return {'data': chat["user_id"] == user_id, 'message': "Association check successful"}


    # Function to Get Chat By Id
    def get_chat_by_id(self, chat_id):
        chat = self.find_document({'_id': bson.ObjectId(chat_id)})
        if chat is not None:
            completions_modified = {}
            for c_time in chat["completions"]:
                completions_modified[c_time] = {
                    'query': chat["completions"][c_time].get('query', None),
                    'article': chat["completions"][c_time].get('article', None),
                    'summary': chat["completions"][c_time].get('summary', None)
                }
            chat["completions"] = completions_modified
            del chat['_id']
            return {'data': chat, 'message': "Successfully retrieved chat"}
        return {'data': None, 'message': "Chat does not exist"}
    

    # Function to Delete all Chats for user
    def purge_chats(self, user_id):
        chats = self.find_documents({'user_id': user_id})
        if not chats:
            return {'data': None, 'message': "No chats found for the user"}

        for chat in chats:
            chat_id = str(chat['_id'])
            self.remove_document({'_id': bson.ObjectId(chat_id)})
            self.user_col.update_user_chats(user_id, chat_id, action="remove")

        return {'data': None, 'message': "All chats deleted successfully"}
