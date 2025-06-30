from bson import ObjectId
from expense_analyzer_backend.services.database import get_db
from expense_analyzer_backend.auth.utils import hash_password, verify_password
from datetime import datetime


class User:
    """User model for database operations"""
    
    def __init__(self, email, name, password=None, _id=None):
        self.email = email
        self.name = name
        self.password = password
        self._id = _id
    
    @classmethod
    def create(cls, email, name, password):
        """Create a new user"""
        db = get_db()
        
        # Check if user already exists
        if db.users.find_one({'email': email}):
            raise ValueError("User with this email already exists")
        
        # Hash password and create user
        hashed_password = hash_password(password)
        user_data = {
            'email': email,
            'name': name,
            'password': hashed_password,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.users.insert_one(user_data)
        return cls(email, name, _id=result.inserted_id)
    
    @classmethod
    def find_by_email(cls, email):
        """Find user by email"""
        db = get_db()
        user_data = db.users.find_one({'email': email})
        
        if user_data:
            return cls(
                email=user_data['email'],
                name=user_data['name'],
                password=user_data['password'],
                _id=user_data['_id']
            )
        return None
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find user by ID"""
        db = get_db()
        user_data = db.users.find_one({'_id': ObjectId(user_id)})
        # print("user data from user.py",user_data)
        
        # print(cls(
        #         email=user_data['email'],
        #         name=user_data['username'],
        #         _id=user_data['_id']
        #     ))
        # print("printed cls(====)")
        
        if user_data:
            print("Returning user data")
            return cls(
                email=user_data['email'],
                name=user_data['username'],
                _id=user_data['_id']
            )
        print("returning None")
        return None
    
    def verify_password(self, password):
        """Verify user password"""
        return verify_password(password, self.password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': str(self._id),
            'email': self.email,
            'name': self.name
        }