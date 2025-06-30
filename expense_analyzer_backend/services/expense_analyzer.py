import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from expense_analyzer_backend.models.expense import Expense
import logging

logger = logging.getLogger(__name__)


class ExpenseAnalyzer:
    """Service for analyzing user expenses and generating insights"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        self.seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    def get_expenses_dataframe(self, start_date=None, end_date=None) -> pd.DataFrame:
        """Get expenses as pandas DataFrame"""
        try:
            expenses = Expense.find_by_user_id(
                self.user_id,
                start_date=start_date or self.thirty_days_ago,
                end_date=end_date
            )
            
            if not expenses:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for expense in expenses:
                data.append({
                    'id': str(expense._id),
                    'amount': expense.amount,
                    'category': expense.category,
                    'description': expense.description,
                    'date': expense.date
                })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = pd.to_numeric(df['amount'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating expenses DataFrame: {e}")
            return pd.DataFrame()
    
    def analyze_spending_by_category(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze spending patterns by category"""
        if df.empty:
            return {}
        
        try:
            category_analysis = df.groupby('category').agg({
                'amount': ['sum', 'count', 'mean', 'min', 'max']
            }).round(2)
            
            category_analysis.columns = ['total_spent', 'transaction_count', 'average_amount', 'min_amount', 'max_amount']
            
            # Convert to dictionary and add percentage
            total_spending = df['amount'].sum()
            result = {}
            
            for category, data in category_analysis.iterrows():
                result[category] = {
                    'total_spent': float(data['total_spent']),
                    'transaction_count': int(data['transaction_count']),
                    'average_amount': float(data['average_amount']),
                    'min_amount': float(data['min_amount']),
                    'max_amount': float(data['max_amount']),
                    'percentage_of_total': round((data['total_spent'] / total_spending) * 100, 2) if total_spending > 0 else 0
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing spending by category: {e}")
            return {}
    
    def get_spending_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze spending trends over time"""
        if df.empty:
            return {}
        
        try:
            # Weekly trends
            df['week'] = df['date'].dt.isocalendar().week
            df['year'] = df['date'].dt.year
            df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str)
            
            weekly_spending = df.groupby('year_week')['amount'].sum().to_dict()
            
            # Calculate trend
            weeks = sorted(weekly_spending.keys())
            trend = "insufficient_data"
            recent_weekly_avg = 0
            earlier_weekly_avg = 0
            
            if len(weeks) >= 2:
                # Compare last 2 weeks vs first 2 weeks
                recent_weeks = weeks[-2:] if len(weeks) >= 2 else weeks[-1:]
                earlier_weeks = weeks[:2] if len(weeks) >= 4 else weeks[:1]
                
                recent_weekly_avg = sum(weekly_spending[w] for w in recent_weeks) / len(recent_weeks)
                earlier_weekly_avg = sum(weekly_spending[w] for w in earlier_weeks) / len(earlier_weeks)
                
                if recent_weekly_avg > earlier_weekly_avg * 1.1:
                    trend = "increasing"
                elif recent_weekly_avg < earlier_weekly_avg * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
            
            # Daily averages
            daily_spending = df.groupby(df['date'].dt.date)['amount'].sum()
            
            return {
                'weekly_spending': weekly_spending,
                'daily_average': round(df['amount'].sum() / 30, 2),
                'trend': trend,
                'recent_weekly_avg': round(recent_weekly_avg, 2),
                'earlier_weekly_avg': round(earlier_weekly_avg, 2),
                'highest_spending_day': {
                    'date': str(daily_spending.idxmax()) if not daily_spending.empty else None,
                    'amount': float(daily_spending.max()) if not daily_spending.empty else 0
                },
                'lowest_spending_day': {
                    'date': str(daily_spending.idxmin()) if not daily_spending.empty else None,
                    'amount': float(daily_spending.min()) if not daily_spending.empty else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spending trends: {e}")
            return {}
    
    def generate_smart_suggestions(self, category_analysis: Dict, trends: Dict, total_spending: float) -> List[Dict]:
        """Generate intelligent spending suggestions"""
        suggestions = []
        
        if not category_analysis:
            return [{
                'type': 'info',
                'message': 'No expense data found for the last 30 days. Start tracking your expenses to get personalized insights!',
                'priority': 'low'
            }]
        
        try:
            # High spending category suggestions
            sorted_categories = sorted(
                category_analysis.items(),
                key=lambda x: x[1]['total_spent'],
                reverse=True
            )
            
            for category, data in sorted_categories[:3]:
                percentage = data['percentage_of_total']
                
                if percentage > 30:
                    suggestions.append({
                        'type': 'warning',
                        'category': category,
                        'message': f"You're spending a lot on {category} ({percentage:.1f}% of total). Consider reducing it by 15-20%.",
                        'current_spending': data['total_spent'],
                        'suggested_reduction': round(data['total_spent'] * 0.175, 2),
                        'priority': 'high'
                    })
                elif percentage > 20:
                    suggestions.append({
                        'type': 'tip',
                        'category': category,
                        'message': f"{category} is your top spending category at ₹{data['total_spent']:.2f}. Consider setting a monthly budget.",
                        'current_spending': data['total_spent'],
                        'priority': 'medium'
                    })
            
            # Trend-based suggestions
            if trends.get('trend') == 'increasing':
                suggestions.append({
                    'type': 'alert',
                    'message': f"Your spending has increased recently. Weekly average went from ₹{trends['earlier_weekly_avg']:.2f} to ₹{trends['recent_weekly_avg']:.2f}.",
                    'trend': 'increasing',
                    'priority': 'high'
                })
            elif trends.get('trend') == 'decreasing':
                suggestions.append({
                    'type': 'positive',
                    'message': f"Great job! Your spending has decreased. You're saving ₹{(trends['earlier_weekly_avg'] - trends['recent_weekly_avg']):.2f} per week on average.",
                    'trend': 'decreasing',
                    'priority': 'low'
                })
            
            # High-frequency spending suggestions
            for category, data in category_analysis.items():
                if data['transaction_count'] > 15:  # More than 15 transactions in 30 days
                    suggestions.append({
                        'type': 'tip',
                        'category': category,
                        'message': f"You made {data['transaction_count']} {category} transactions this month. Consider consolidating purchases to reduce impulse spending.",
                        'transaction_count': data['transaction_count'],
                        'priority': 'medium'
                    })
            
            # Budget suggestions
            if total_spending > 0:
                suggested_budget = round(total_spending * 0.9, 2)
                suggestions.append({
                    'type': 'budget',
                    'message': f"Based on your spending pattern, consider setting a monthly budget of ₹{suggested_budget:.2f} to save 10%.",
                    'current_spending': total_spending,
                    'suggested_budget': suggested_budget,
                    'priority': 'medium'
                })
            
            # Sort suggestions by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            suggestions.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 1), reverse=True)
            
            return suggestions if suggestions else [{
                'type': 'positive',
                'message': 'Your spending looks well-balanced! Keep up the good work with tracking your expenses.',
                'priority': 'low'
            }]
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return [{
                'type': 'error',
                'message': 'Unable to generate suggestions at this time. Please try again later.',
                'priority': 'low'
            }]
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """Get comprehensive expense analysis"""
        try:
            # Get data
            df = self.get_expenses_dataframe()
            
            if df.empty:
                return {
                    'success': True,
                    'data': {
                        'total_expenses': 0,
                        'expense_count': 0,
                        'category_analysis': {},
                        'trends': {},
                        'suggestions': [{
                            'type': 'info',
                            'message': 'No expense data found for the last 30 days. Start adding expenses to get personalized insights!',
                            'priority': 'low'
                        }],
                        'period': '30 days',
                        'analysis_date': datetime.utcnow().isoformat()
                    }
                }
            
            # Perform analysis
            total_spending = float(df['amount'].sum())
            category_analysis = self.analyze_spending_by_category(df)
            trends = self.get_spending_trends(df)
            suggestions = self.generate_smart_suggestions(category_analysis, trends, total_spending)
            
            return {
                'success': True,
                'data': {
                    'total_expenses': round(total_spending, 2),
                    'expense_count': len(df),
                    'category_analysis': category_analysis,
                    'trends': trends,
                    'suggestions': suggestions,
                    'period': '30 days',
                    'analysis_date': datetime.utcnow().isoformat(),
                    'average_daily_spending': round(total_spending / 30, 2),
                    'top_category': max(category_analysis.items(), key=lambda x: x[1]['total_spent'])[0] if category_analysis else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to analyze expenses'
            }