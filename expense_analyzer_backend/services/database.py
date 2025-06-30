from pymongo import MongoClient
from flask import current_app, g
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for MongoDB operations"""
    
    def __init__(self, app=None):
        self.client = None
        self.db = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize database with Flask app"""
        try:
            self.client = MongoClient(app.config['MONGO_URI'])
            self.db = self.client[app.config['DATABASE_NAME']]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Create indexes
            self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # User indexes
            self.db.users.create_index("email", unique=True)
            
            # Expense indexes
            self.db.expenses.create_index([("userId", 1), ("date", -1)])
            self.db.expenses.create_index([("userId", 1), ("category", 1)])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    def get_db(self):
        """Get database instance"""
        return self.db


# Global database instance
db_service = DatabaseService()


def init_db(app):
    """Initialize database with app"""
    db_service.init_app(app)


def get_db():
    """Get database instance for current request"""
    return db_service.get_db()