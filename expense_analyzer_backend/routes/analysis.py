from flask import Blueprint, request, jsonify,g
from expense_analyzer_backend.auth.middleware import authenticate_token
from expense_analyzer_backend.services.expense_analyzer import ExpenseAnalyzer
from expense_analyzer_backend.models.expense import Expense
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/comprehensive', methods=['GET'])
@authenticate_token
def get_comprehensive_analysis():
    """Get comprehensive expense analysis with smart suggestions"""
    try:
        user_id = str(g.user._id)
        analyzer = ExpenseAnalyzer(user_id)
        
        analysis = analyzer.get_comprehensive_analysis()
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to analyze expenses',
            'error': str(e)
        }), 500


@analysis_bp.route('/category/<category>', methods=['GET'])
@authenticate_token
def get_category_insights(category):
    """Get detailed insights for a specific category"""
    try:
        user_id = str(g.user._id)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get category-specific expenses
        expenses = Expense.find_by_user_id(
            user_id=user_id,
            start_date=thirty_days_ago,
            category=category
        )
        
        if not expenses:
            return jsonify({
                'success': True,
                'data': {
                    'category': category,
                    'message': f'No {category} expenses found in the last 30 days.',
                    'total_spent': 0,
                    'transaction_count': 0
                }
            })
        
        # Calculate insights
        amounts = [expense.amount for expense in expenses]
        total_spent = sum(amounts)
        
        insights = {
            'category': category,
            'total_spent': round(total_spent, 2),
            'transaction_count': len(expenses),
            'average_transaction': round(sum(amounts) / len(amounts), 2),
            'highest_expense': max(amounts),
            'lowest_expense': min(amounts),
            'daily_average': round(total_spent / 30, 2),
            'recent_transactions': [expense.to_dict() for expense in expenses[-5:]]
        }
        
        return jsonify({
            'success': True,
            'data': insights
        })
        
    except Exception as e:
        logger.error(f"Error getting category insights: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get category insights',
            'error': str(e)
        }), 500


@analysis_bp.route('/summary', methods=['GET'])
@authenticate_token
def get_spending_summary():
    """Get spending summary across different time periods"""
    try:
        user_id = str(g.user._id)
        now = datetime.utcnow()
        
        # Define time periods
        periods = {
            'last_7_days': now - timedelta(days=7),
            'last_30_days': now - timedelta(days=30),
            'last_90_days': now - timedelta(days=90)
        }
        
        summary = {}
        
        for period_name, start_date in periods.items():
            expenses = Expense.find_by_user_id(user_id, start_date=start_date)
            
            if expenses:
                amounts = [expense.amount for expense in expenses]
                categories = {}
                
                for expense in expenses:
                    if expense.category in categories:
                        categories[expense.category] += expense.amount
                    else:
                        categories[expense.category] = expense.amount
                
                top_category = max(categories.items(), key=lambda x: x[1]) if categories else (None, 0)
                
                summary[period_name] = {
                    'total_spent': round(sum(amounts), 2),
                    'transaction_count': len(expenses),
                    'average_transaction': round(sum(amounts) / len(amounts), 2),
                    'top_category': top_category[0],
                    'top_category_amount': round(top_category[1], 2)
                }
            else:
                summary[period_name] = {
                    'total_spent': 0,
                    'transaction_count': 0,
                    'average_transaction': 0,
                    'top_category': None,
                    'top_category_amount': 0
                }
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting spending summary: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get spending summary',
            'error': str(e)
        }), 500


@analysis_bp.route('/trends', methods=['GET'])
@authenticate_token
def get_spending_trends():
    """Get detailed spending trends"""
    try:
        user_id = str(g.user._id)
        
        # Get date range from query params
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        analyzer = ExpenseAnalyzer(user_id)
        df = analyzer.get_expenses_dataframe(start_date=start_date)
        
        if df.empty:
            return jsonify({
                'success': True,
                'data': {
                    'message': f'No expense data found for the last {days} days.',
                    'trends': {}
                }
            })
        
        trends = analyzer.get_spending_trends(df)
        
        return jsonify({
            'success': True,
            'data': {
                'period_days': days,
                'trends': trends
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting spending trends: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get spending trends',
            'error': str(e)
        }), 500