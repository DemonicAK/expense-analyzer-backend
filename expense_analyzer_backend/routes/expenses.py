from flask import Blueprint, request, jsonify,g
from expense_analyzer_backend.auth.middleware import authenticate_token
from expense_analyzer_backend.models.expense import Expense
from expense_analyzer_backend.utils.validators import validate_expense_data
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

expenses_bp = Blueprint('expenses', __name__)


@expenses_bp.route('', methods=['GET'])
@authenticate_token
def get_expenses():
    """Get user's expenses with optional filters"""
    try:
        user_id = str(g.user._id)
        
        # Get query parameters
        category = request.args.get('category')
        limit = request.args.get('limit', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Get expenses
        expenses = Expense.find_by_user_id(
            user_id=user_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            category=category,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': [expense.to_dict() for expense in expenses],
            'count': len(expenses)
        })
        
    except Exception as e:
        logger.error(f"Error fetching expenses: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch expenses',
            'error': str(e)
        }), 500


@expenses_bp.route('', methods=['POST'])
@authenticate_token
def create_expense():
    """Create a new expense"""
    try:
        data = request.get_json()
        
        # Validate data
        validation_error = validate_expense_data(data)
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        user_id = str(g.user._id)
        
        # Parse date if provided
        expense_date = None
        if data.get('date'):
            try:
                expense_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        # Create expense
        expense = Expense.create(
            user_id=user_id,
            amount=data['amount'],
            category=data['category'],
            description=data['description'],
            date=expense_date
        )
        
        return jsonify({
            'success': True,
            'data': expense.to_dict(),
            'message': 'Expense created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to create expense',
            'error': str(e)
        }), 500


@expenses_bp.route('/<expense_id>', methods=['GET'])
@authenticate_token
def get_expense(expense_id):
    """Get a specific expense"""
    try:
        user_id = str(g.user._id)
        expense = Expense.find_by_id(expense_id, user_id)
        
        if not expense:
            return jsonify({
                'success': False,
                'message': 'Expense not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': expense.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error fetching expense: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch expense',
            'error': str(e)
        }), 500


@expenses_bp.route('/<expense_id>', methods=['PUT'])
@authenticate_token
def update_expense(expense_id):
    """Update an expense"""
    try:
        data = request.get_json()
        user_id = str(g.user._id)
        
        expense = Expense.find_by_id(expense_id, user_id)
        if not expense:
            return jsonify({
                'success': False,
                'message': 'Expense not found'
            }), 404
        
        # Validate update data
        update_data = {}
        if 'amount' in data:
            try:
                update_data['amount'] = float(data['amount'])
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid amount'}), 400
        
        if 'category' in data:
            if not data['category'].strip():
                return jsonify({'error': 'Category cannot be empty'}), 400
            update_data['category'] = data['category'].strip()
        
        if 'description' in data:
            update_data['description'] = data['description'].strip()
        
        if 'date' in data:
            try:
                update_data['date'] = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        # Update expense
        expense.update(**update_data)
        
        return jsonify({
            'success': True,
            'data': expense.to_dict(),
            'message': 'Expense updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating expense: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update expense',
            'error': str(e)
        }), 500


@expenses_bp.route('/<expense_id>', methods=['DELETE'])
@authenticate_token
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        user_id = str(g.user._id)
        expense = Expense.find_by_id(expense_id, user_id)
        
        if not expense:
            return jsonify({
                'success': False,
                'message': 'Expense not found'
            }), 404
        
        expense.delete()
        
        return jsonify({
            'success': True,
            'message': 'Expense deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting expense: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete expense',
            'error': str(e)
        }), 500


@expenses_bp.route('/categories', methods=['GET'])
@authenticate_token
def get_categories():
    """Get all unique categories for the user"""
    try:
        user_id = str(g.user._id)
        expenses = Expense.find_by_user_id(user_id, limit=1000)  # Get recent expenses
        
        categories = list(set(expense.category for expense in expenses))
        categories.sort()
        
        return jsonify({
            'success': True,
            'data': categories
        })
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch categories',
            'error': str(e)
        }), 500