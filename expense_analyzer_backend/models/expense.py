from bson import ObjectId
from expense_analyzer_backend.services.database import get_db
from datetime import datetime
from typing import List, Dict, Optional


class Expense:
    """Expense model for database operations"""
    
    def __init__(self, user_id, amount, category, description, date=None, _id=None):
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        self.amount = float(amount)
        self.category = category
        self.description = description
        self.date = date or datetime.utcnow()
        self._id = _id
    
    @classmethod
    def create(cls, user_id, amount, category, description, date=None):
        """Create a new expense"""
        db = get_db()
        
        expense_data = {
            'userId': ObjectId(user_id),
            'amount': float(amount),
            'category': category,
            'description': description,
            'date': date or datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.expenses.insert_one(expense_data)
        return cls(user_id, amount, category, description, date, _id=result.inserted_id)
    
    @classmethod
    def find_by_user_id(cls, user_id, start_date=None, end_date=None, 
                       category=None, limit=None) -> List['Expense']:
        """Find expenses by user ID with optional filters"""
        db = get_db()
        
        query = {'userId': ObjectId(user_id)}
        
        # Add date filter
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['$gte'] = start_date
            if end_date:
                date_filter['$lte'] = end_date
            query['date'] = date_filter
        
        # Add category filter
        if category:
            query['category'] = category
        
        cursor = db.expenses.find(query).sort('date', -1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        expenses = []
        for expense_data in cursor:
            expenses.append(cls(
                user_id=expense_data['userId'],
                amount=expense_data['amount'],
                category=expense_data['category'],
                description=expense_data['description'],
                date=expense_data['date'],
                _id=expense_data['_id']
            ))
        
        return expenses
    
    @classmethod
    def find_by_id(cls, expense_id, user_id):
        """Find expense by ID and user ID"""
        db = get_db()
        expense_data = db.expenses.find_one({
            '_id': ObjectId(expense_id),
            'userId': ObjectId(user_id)
        })
        
        if expense_data:
            return cls(
                user_id=expense_data['userId'],
                amount=expense_data['amount'],
                category=expense_data['category'],
                description=expense_data['description'],
                date=expense_data['date'],
                _id=expense_data['_id']
            )
        return None
    
    def update(self, **kwargs):
        """Update expense"""
        db = get_db()
        
        update_data = {'updated_at': datetime.utcnow()}
        
        if 'amount' in kwargs:
            update_data['amount'] = float(kwargs['amount'])
            self.amount = float(kwargs['amount'])
        
        if 'category' in kwargs:
            update_data['category'] = kwargs['category']
            self.category = kwargs['category']
        
        if 'description' in kwargs:
            update_data['description'] = kwargs['description']
            self.description = kwargs['description']
        
        if 'date' in kwargs:
            update_data['date'] = kwargs['date']
            self.date = kwargs['date']
        
        db.expenses.update_one(
            {'_id': self._id},
            {'$set': update_data}
        )
    
    def delete(self):
        """Delete expense"""
        db = get_db()
        db.expenses.delete_one({'_id': self._id})
    
    def to_dict(self):
        """Convert expense to dictionary"""
        return {
            'id': str(self._id),
            'user_id': str(self.user_id),
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'date': self.date.isoformat()
        }