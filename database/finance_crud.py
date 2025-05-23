from database.db_connection import create_db_connection
from datetime import datetime, timedelta
import json
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from database.db_connection import create_db_connection


def store_transaction(data):
    """Store a new transaction"""
    conn = create_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transactions 
            (user_id, amount, transaction_type, category, description, card_number)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['user_id'],
            data['amount'],
            data['transaction_type'],
            data['category'],
            data['description'],
            data.get('card_number', None)
        ))
        
        transaction_id = cur.fetchone()[0]
        conn.commit()
        return transaction_id
    except Exception as e:
        print(f"Error storing transaction: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_user_transactions(user_id, start_date=None, end_date=None):
    """Get user transactions with optional date range"""
    conn = create_db_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        query = """
            SELECT 
                id,
                amount,
                transaction_type,
                category,
                description,
                card_number,
                transaction_date::text,
                created_at::text
            FROM transactions 
            WHERE user_id = %s
        """
        params = [user_id]
        
        if start_date:
            query += " AND transaction_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND transaction_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY transaction_date DESC LIMIT 10"
        
        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        transactions = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        return transactions
    except Exception as e:
        print(f"Error getting transactions: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_user_summary(user_id):
    """Get user's financial summary"""
    conn = create_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        # Get current month transactions
        cur.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 0) as total_expenses
            FROM transactions 
            WHERE user_id = %s 
            AND transaction_date >= date_trunc('month', CURRENT_DATE)
        """, (user_id,))
        
        current = cur.fetchone()
        current_income, current_expenses = float(current[0]), float(current[1])

        # If no current month income, get the latest income transaction
        if current_income == 0:
            cur.execute("""
                SELECT amount 
                FROM transactions 
                WHERE user_id = %s AND transaction_type = 'income'
                ORDER BY transaction_date DESC
                LIMIT 1
            """, (user_id,))
            
            latest_income = cur.fetchone()
            if latest_income:
                current_income = float(latest_income[0])

        # Get last month transactions
        cur.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 0) as total_expenses
            FROM transactions 
            WHERE user_id = %s 
            AND transaction_date >= date_trunc('month', CURRENT_DATE - interval '1 month')
            AND transaction_date < date_trunc('month', CURRENT_DATE)
        """, (user_id,))
        
        last = cur.fetchone()
        last_income, last_expenses = float(last[0]), float(last[1])

        # Calculate trends
        income_trend = ((current_income - last_income) / last_income * 100) if last_income > 0 else 0
        expense_trend = ((current_expenses - last_expenses) / last_expenses * 100) if last_expenses > 0 else 0
        disposable_income = current_income - current_expenses
        last_disposable = last_income - last_expenses
        disposable_trend = ((disposable_income - last_disposable) / last_disposable * 100) if last_disposable > 0 else 0

        return {
            "income": current_income,
            "income_trend": income_trend,
            "expenses": current_expenses,
            "expenses_trend": expense_trend,
            "disposable_income": disposable_income,
            "disposable_trend": disposable_trend,
            "savings_potential": current_income * 0.2  # 20% of income
        }
    except Exception as e:
        print(f"Error getting user summary: {e}")
        return None
    finally:
        if conn:
            conn.close()
            
def store_prediction(prediction_data):
    """Store financial prediction in database with proper decimal handling"""
    conn = create_db_connection()
    if not conn:
        return False

    try:
        # Delete old predictions first
        if not delete_old_predictions(prediction_data['user_id']):
            print("Warning: Failed to delete old predictions")

        # Convert and round all numeric values to Decimal
        db_data = {
            'user_id': prediction_data['user_id'],
            'total_income': Decimal(str(prediction_data['total_income'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'total_expenses': Decimal(str(prediction_data['total_expenses'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'disposable_income': Decimal(str(prediction_data['disposable_income'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'savings_potential': Decimal(str(prediction_data['savings_potential'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'confidence_score': Decimal(str(prediction_data['confidence_score'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'prediction_period': prediction_data['prediction_period']
        }

        cur = conn.cursor()
        # Add created_at timestamp explicitly
        cur.execute("""
            INSERT INTO predictions 
            (user_id, total_income, total_expenses, disposable_income, 
             savings_potential, confidence_score, prediction_period, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            db_data['user_id'],
            db_data['total_income'],
            db_data['total_expenses'],
            db_data['disposable_income'],
            db_data['savings_potential'],
            db_data['confidence_score'],
            db_data['prediction_period'],
            datetime.now()  # Add current timestamp
        ))
        
        prediction_id = cur.fetchone()[0]
        conn.commit()
        print(f"Successfully stored new prediction with ID: {prediction_id}")
        return prediction_id
    except Exception as e:
        print(f"Error storing prediction: {type(e).__name__} - {str(e)}")
        print(f"Prediction data: {prediction_data}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_latest_prediction(user_id):
    """Get user's most recent prediction with proper decimal handling"""
    conn = create_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                id,
                total_income,
                total_expenses,
                disposable_income,
                savings_potential,
                confidence_score,
                prediction_period,
                created_at::text
            FROM predictions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        
        row = cur.fetchone()
        if not row:
            return None
            
        return {
            'id': row[0],
            'total_income': Decimal(str(row[1])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'total_expenses': Decimal(str(row[2])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'disposable_income': Decimal(str(row[3])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'savings_potential': Decimal(str(row[4])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'confidence_score': Decimal(str(row[5])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'prediction_period': row[6],
            'created_at': row[7]
        }
    except Exception as e:
        print(f"Error getting latest prediction: {type(e).__name__} - {str(e)}")
        return None
    finally:
        if conn:
            conn.close()
            
            
def delete_old_predictions(user_id):
    """Delete all previous predictions for a user"""
    conn = create_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM predictions 
            WHERE user_id = %s
        """, (user_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting old predictions: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()



def get_user_data(email):
    conn = create_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, fullname, email, phone, gender, dob, occupation, city_tier 
            FROM users WHERE email = %s
        """, (email,))
        
        row = cur.fetchone()
        if not row:
            return None
        
        columns = ['id', 'fullname', 'email', 'phone', 'gender', 'dob', 'occupation', 'city_tier']
        return dict(zip(columns, row))
    
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return None
    
    finally:
        if conn:
            conn.close()
