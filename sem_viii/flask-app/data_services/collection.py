import bson

class _Collection:
    def __init__(self, collection):
        self._collection = collection


    # Function to insert a new document
    def insert_document(self, doc):
        return self._collection.insert_one(doc)


    # Function to retrieve document
    def find_document(self, _filter):
        return self._collection.find_one(_filter)
    

    # Function to retrieve documents
    def find_documents(self, _filter):
        return self._collection.find(_filter)
    

    # Function to retrieve delete a document
    def remove_document(self, _filter):
        return self._collection.delete_one(_filter)
    

    # Function to update a document
    def update_document(self, _filter, _operation):
        return self._collection.update_one(_filter, _operation)


    # Function to verify the presence of an object
    def verify(self, object_id):
        return not (self._collection.find_one({"_id" : bson.ObjectId(object_id)}) is None)
        