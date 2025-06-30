from typing import Dict, Optional


def validate_expense_data(data: Dict) -> Optional[str]:
    """Validate expense data"""
    if not data:
        return "Request body is required"
    
    required_fields = ['amount', 'category', 'description']
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"
    
    # Validate amount
    try:
        amount = float(data['amount'])
        if amount <= 0:
            return "Amount must be greater than 0"
    except (ValueError, TypeError):
        return "Invalid amount format"
    
    # Validate category
    if not isinstance(data['category'], str) or not data['category'].strip():
        return "Category must be a non-empty string"
    
    # Validate description
    if not isinstance(data['description'], str):
        return "Description must be a string"
    
    return None


def validate_user_data(data: Dict) -> Optional[str]:
    """Validate user registration data"""
    if not data:
        return "Request body is required"
    
    required_fields = ['email', 'name', 'password']
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"
    
    # Validate email
    email = data['email']
    if not isinstance(email, str) or '@' not in email:
        return "Invalid email format"
    
    # Validate name
    if not isinstance(data['name'], str) or not data['name'].strip():
        return "Name must be a non-empty string"
    
    # Validate password
    if not isinstance(data['password'], str) or len(data['password']) < 6:
        return "Password must be at least 6 characters long"
    
    return None