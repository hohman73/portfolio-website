# MongoDB Connection

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
class Database:
    def __init__(self):
        # Get MongoDB URI from environment variable
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.database_name = os.getenv("DATABASE_NAME", "portfolio_db")
        
        # Initialize client and database
        self.client = None
        self.db = None
        
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            # Test the connection
            self.client.server_info()
            print(f"✅ Connected to MongoDB: {self.database_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    def get_collection(self, collection_name):
        """Get a specific collection"""
        if self.db is not None:
            return self.db[collection_name]
        else:
            raise Exception("Database not connected")
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("🔌 MongoDB connection closed")

# Create database instance
db = Database()

# Collections
def get_projects_collection():
    return db.get_collection("projects")

def get_contacts_collection():
    return db.get_collection("contacts")