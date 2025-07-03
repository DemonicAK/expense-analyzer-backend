from flask import Blueprint, request, jsonify, current_app, g
from datetime import datetime, date
import calendar
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from collections import defaultdict
from bson import ObjectId
from expense_analyzer_backend.auth.middleware import authenticate_token
from expense_analyzer_backend.services.database import get_db
import logging

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)


def get_pg_conn():
    """Get PostgreSQL connection"""
    return psycopg2.connect(current_app.config['SUPABASE_DB_URL'])


def get_monthly_expenses(user_id, month, year):
    """Fetch expenses from MongoDB for a specific month"""
    try:
        db = get_db()
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        expenses = list(db.expenses.find({
            'userId': ObjectId(user_id),
            'date': {
                '$gte': start_date,
                '$lt': end_date
            }
        }))
        
        return expenses
    except Exception as e:
        logger.error(f"Error fetching monthly expenses: {e}")
        return []


def calculate_report_data(expenses, user_id, month, year):
    """Calculate report metrics from expenses"""
    if not expenses:
        return {
            'totalSpent': 0,
            'topCategory': None,
            'overbudgetCategories': []
        }
    
    total_spent = sum(exp['amount'] for exp in expenses)
    
    # Group by category
    category_totals = {}
    for exp in expenses:
        category = exp['category']
        if category in category_totals:
            category_totals[category] += exp['amount']
        else:
            category_totals[category] = exp['amount']
    
    # Find top category
    top_category = max(category_totals, key=category_totals.get) if category_totals else None
    
    # Check overbudget categories
    overbudget_categories = check_overbudget_categories(category_totals, user_id)
    
    return {
        'totalSpent': float(total_spent),
        'topCategory': top_category,
        'overbudgetCategories': overbudget_categories,
        'categoryBreakdown': {k: float(v) for k, v in category_totals.items()},
        'transactionCount': len(expenses)
    }


def check_overbudget_categories(category_totals, user_id):
    """Check which categories are over budget"""
    # TODO: Implement budget fetching logic when you have budget feature
    # For now, returning empty list
    overbudget = []
    
    # Example implementation (uncomment when budget feature is ready):
    # try:
    #     db = get_db()
    #     budgets = db.budgets.find({'userId': ObjectId(user_id)})
    #     for budget in budgets:
    #         category = budget['category']
    #         if category in category_totals and category_totals[category] > budget['limitAmount']:
    #             overbudget.append(category)
    # except Exception as e:
    #     logger.error(f"Error checking overbudget categories: {e}")
    
    return overbudget


def save_monthly_report(user_id, month, year, report_data):
    """Save report to PostgreSQL"""
    try:
        with get_pg_conn() as pg_conn:
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS monthly_reports (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(50) NOT NULL,
                        month INTEGER NOT NULL,
                        year INTEGER NOT NULL,
                        total_spent DECIMAL(10,2) NOT NULL,
                        top_category VARCHAR(100),
                        overbudget_categories JSONB,
                        category_breakdown JSONB,
                        transaction_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, month, year)
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO monthly_reports 
                    (user_id, month, year, total_spent, top_category, overbudget_categories, category_breakdown, transaction_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, month, year) 
                    DO UPDATE SET 
                        total_spent = EXCLUDED.total_spent,
                        top_category = EXCLUDED.top_category,
                        overbudget_categories = EXCLUDED.overbudget_categories,
                        category_breakdown = EXCLUDED.category_breakdown,
                        transaction_count = EXCLUDED.transaction_count,
                        created_at = CURRENT_TIMESTAMP
                """, (
                    user_id,
                    month,
                    year,
                    report_data['totalSpent'],
                    report_data['topCategory'],
                    json.dumps(report_data['overbudgetCategories']),
                    json.dumps(report_data['categoryBreakdown']),
                    report_data['transactionCount']
                ))
                pg_conn.commit()
    except Exception as e:
        logger.error(f"Error saving monthly report: {e}")
        raise


def generate_monthly_report(user_id, month, year):
    """Generate and save monthly report for a user"""
    try:
        # Fetch expenses from MongoDB
        expenses = get_monthly_expenses(user_id, month, year)
        
        # Calculate report data
        report_data = calculate_report_data(expenses, user_id, month, year)
        
        # Save to PostgreSQL
        save_monthly_report(user_id, month, year, report_data)
        
        return report_data
    except Exception as e:
        logger.error(f"Error generating report for user {user_id}: {str(e)}")
        return None


@reports_bp.route('/generate', methods=['POST'])
@authenticate_token
def generate_report():
    """Manually generate a monthly report"""
    try:
        data = request.get_json()
        user_id = str(g.user._id)
        month = data.get('month')
        year = data.get('year')
        
        if not all([month, year]):
            return jsonify({'error': 'Missing required fields: month, year'}), 400
        
        if not (1 <= month <= 12):
            return jsonify({'error': 'Month must be between 1 and 12'}), 400
        
        if year < 2020 or year > datetime.now().year:
            return jsonify({'error': 'Invalid year'}), 400
        
        report_data = generate_monthly_report(user_id, month, year)
        
        if report_data:
            return jsonify({
                'success': True,
                'data': report_data,
                'message': f'Report generated for {month}/{year}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate report'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in generate_report: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to generate report',
            'error': str(e)
        }), 500


@reports_bp.route('', methods=['GET'])
@authenticate_token
def get_user_reports():
    """Get past 3 months reports for current user"""
    try:
        user_id = str(g.user._id)
        
        with get_pg_conn() as pg_conn:
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM monthly_reports 
                    WHERE user_id = %s 
                    ORDER BY year DESC, month DESC 
                    LIMIT 3
                """, (user_id,))
                
                reports = cursor.fetchall()
                
                # Convert to list of dicts and parse JSON fields
                result = []
                for report in reports:
                    report_dict = dict(report)
                    report_dict['overbudget_categories'] = json.loads(report_dict['overbudget_categories']) if report_dict['overbudget_categories'] else []
                    report_dict['category_breakdown'] = json.loads(report_dict['category_breakdown']) if report_dict['category_breakdown'] else {}
                    result.append(report_dict)
                
                return jsonify({
                    'success': True,
                    'data': result
                })
                
    except Exception as e:
        logger.error(f"Error getting user reports: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch reports',
            'error': str(e)
        }), 500


@reports_bp.route('/all', methods=['GET'])
@authenticate_token
def get_all_user_reports():
    """Get all reports for current user"""
    try:
        user_id = str(g.user._id)
        
        with get_pg_conn() as pg_conn:
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM monthly_reports 
                    WHERE user_id = %s 
                    ORDER BY year DESC, month DESC
                """, (user_id,))
                
                reports = cursor.fetchall()
                
                result = []
                for report in reports:
                    report_dict = dict(report)
                    report_dict['overbudget_categories'] = json.loads(report_dict['overbudget_categories']) if report_dict['overbudget_categories'] else []
                    report_dict['category_breakdown'] = json.loads(report_dict['category_breakdown']) if report_dict['category_breakdown'] else {}
                    result.append(report_dict)
                
                return jsonify({
                    'success': True,
                    'data': result
                })
                
    except Exception as e:
        logger.error(f"Error getting all user reports: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch reports',
            'error': str(e)
        }), 500


@reports_bp.route('/<int:year>/<int:month>', methods=['GET'])
@authenticate_token
def get_specific_report(year, month):
    """Get a specific month's report"""
    try:
        user_id = str(g.user._id)
        
        if not (1 <= month <= 12):
            return jsonify({'error': 'Month must be between 1 and 12'}), 400
        
        with get_pg_conn() as pg_conn:
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM monthly_reports 
                    WHERE user_id = %s AND year = %s AND month = %s
                """, (user_id, year, month))
                
                report = cursor.fetchone()
                
                if report:
                    report_dict = dict(report)
                    report_dict['overbudget_categories'] = json.loads(report_dict['overbudget_categories']) if report_dict['overbudget_categories'] else []
                    report_dict['category_breakdown'] = json.loads(report_dict['category_breakdown']) if report_dict['category_breakdown'] else {}
                    
                    return jsonify({
                        'success': True,
                        'data': report_dict
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'No report found for {month}/{year}'
                    }), 404
                
    except Exception as e:
        logger.error(f"Error getting specific report: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch report',
            'error': str(e)
        }), 500


def generate_all_monthly_reports():
    """Generate reports for all users for the previous month"""
    try:
        # Get previous month
        today = date.today()
        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year
        
        # Get all users from MongoDB
        db = get_db()
        users = list(db.users.find({}, {'_id': 1}))
        
        logger.info(f"Generating reports for {len(users)} users for {prev_month}/{prev_year}")
        
        success_count = 0
        for user in users:
            user_id = str(user['_id'])
            report_data = generate_monthly_report(user_id, prev_month, prev_year)
            if report_data:
                success_count += 1
                logger.info(f"Generated report for user {user_id}")
            else:
                logger.error(f"Failed to generate report for user {user_id}")
        
        logger.info(f"Successfully generated {success_count}/{len(users)} reports")
                
    except Exception as e:
        logger.error(f"Error in scheduled report generation: {str(e)}")