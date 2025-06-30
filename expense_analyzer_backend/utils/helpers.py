from datetime import datetime
from typing import Any, Dict


def format_currency(amount: float, currency: str = '₹') -> str:
    """Format amount as currency"""
    return f"{currency}{amount:,.2f}"


def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format"""
    return dt.isoformat()


def parse_datetime(date_string: str) -> datetime:
    """Parse datetime from string"""
    return datetime.fromisoformat(date_string.replace('Z', '+00:00'))


def success_response(data: Any = None, message: str = None) -> Dict:
    """Create success response"""
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return response


def error_response(message: str, error: str = None) -> Dict:
    """Create error response"""
    response = {'success': False, 'message': message}
    if error:
        response['error'] = error
    return response