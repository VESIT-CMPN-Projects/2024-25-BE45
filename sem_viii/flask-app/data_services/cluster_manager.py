import time
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient


class ClusterManager:
    def __init__(self, mongo_uri, retries=2, _off=30):
        self.connect_success = False

        for _ in range(retries):
            if self.connect(mongo_uri):
                break
            print(f"Trying again in {_off}s")
            time.sleep(_off)

        if not self.connect_success:
            raise ("Cannot connect to MongoDB")


    # Function to instantiate client
    def connect(self, MONGODB_URI):
        try:
            self.client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
            self.connect_success = self.ping()
        except Exception as e:
            print(f"Connection to MongoDB Failed: {e}")
        return self.connect_success
    

    # Function to ping MongoServer from client
    def ping(self):
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
            return True
        except Exception as e:
            print(e)
            return False 


    # Function to list all the databases in the cluster
    def list_databases(self):
        if self.connect_success:
            db_list = self.client.list_database_names()
            if len(db_list) == 0:
                print("[Empty]")
            else:
                for db_name in db_list:
                    print(db_name)
        raise Exception("Please connect to MongoDB!")


    # Function to get a reference to a database
    def get_database(self, db_name):
        if self.connect_success:
            try:
                db = self.client[db_name]
                # c = db['hi']
                # c.find_one
                return db
            except: 
                raise ValueError(f"There does not exists a database by the name {db_name}")
        raise Exception("Please connect to MongoDB!")


    # Function to list all the collections in the database
    def list_collections(self, db):
        if self.connect_success:
            col_list = db.list_collection_names()
            if len(col_list) == 0:
                print("[Empty]")
            else:
                for col_name in col_list:
                    print(col_name)
        raise Exception("Please connect to MongoDB!")


    # Function to get a reference to a collection
    def get_collection(self, db_name, collection_name):   
        db = self.get_database(db_name)
        if self.connect_success and db is not None:
            try:
                collection = db[collection_name]
                return collection
            except: 
                raise ValueError(f"There does not exists a collection by the name {collection_name}")
        raise Exception("Please connect to MongoDB!")
