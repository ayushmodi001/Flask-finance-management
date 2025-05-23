from database.db_connection import create_db_connection
from datetime import datetime
import hashlib

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(fullname, username, email, phone, gender, dob, password):
    """Insert a new user into the database."""
    conn = create_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        
        # First check if user already exists
        cur.execute(
            "SELECT id FROM users WHERE email = %s OR username = %s",
            (email, username)
        )
        if cur.fetchone():
            print(f"User already exists with email {email} or username {username}")
            return False

        # Hash the password
        hashed_password = hash_password(password)

        # Insert new user
        cur.execute(
            """
            INSERT INTO users (
                fullname, 
                username, 
                email, 
                phone, 
                gender, 
                dob, 
                password,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                fullname, 
                username, 
                email, 
                phone, 
                gender, 
                dob, 
                hashed_password,
                datetime.now()
            )
        )
        
        user_id = cur.fetchone()[0]
        conn.commit()

        # Create initial financial data
        create_initial_financial_data(user_id)
        
        return True
    except Exception as e:
        print(f"Error during signup: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def login_user(email, password):
    """Check if the user exists and return authentication status."""
    conn = create_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        # Hash the password for comparison
        hashed_password = hash_password(password)
        
        cur.execute(
            """
            SELECT id, email, fullname 
            FROM users 
            WHERE email = %s AND password = %s
            """,
            (email, hashed_password)
        )
        user = cur.fetchone()
        return user is not None
    except Exception as e:
        print(f"Error during login: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_user_data(email):
    """Get user data by email."""
    conn = create_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                id, 
                fullname, 
                username, 
                email, 
                phone, 
                gender, 
                dob, 
                created_at 
            FROM users 
            WHERE email = %s
            """,
            (email,)
        )
        user = cur.fetchone()
        
        if not user:
            return None
            
        return {
            "id": user[0],
            "fullname": user[1],
            "username": user[2],
            "email": user[3],
            "phone": user[4],
            "gender": user[5],
            "dob": user[6],
            "created_at": user[7]
        }
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return None
    finally:
        conn.close()

def get_all_users():
    """Get all users from the database."""
    conn = create_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                id, 
                fullname, 
                username, 
                email, 
                phone, 
                gender, 
                dob, 
                created_at 
            FROM users
            """
        )
        users = cur.fetchall()
        
        if not users:
            return []
            
        return [
            {
                "id": user[0],
                "fullname": user[1],
                "username": user[2],
                "email": user[3],
                "phone": user[4],
                "gender": user[5],
                "dob": user[6],
                "created_at": user[7]
            }
            for user in users
        ]
    except Exception as e:
        print(f"Error fetching all users: {e}")
        return []
    finally:
        conn.close()

def create_initial_financial_data(user_id):
    """Create initial financial data for new user."""
    conn = create_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        
        # Create initial prediction
        cur.execute(
            """
            INSERT INTO predictions (
                user_id, 
                total_income, 
                total_expenses, 
                disposable_income,
                savings_potential,
                confidence_score,
                prediction_period
            )
            VALUES (%s, 0, 0, 0, 0, 85.0, 'Monthly')
            """,
            (user_id,)
        )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating initial financial data: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def update_user_profile(email, update_data):
    """Update user profile information."""
    conn = create_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        
        # Build update query dynamically based on provided fields
        update_fields = []
        update_values = []
        for key, value in update_data.items():
            if value is not None:
                update_fields.append(f"{key} = %s")
                update_values.append(value)
        
        if not update_fields:
            return False
            
        update_values.append(email)  # Add email for WHERE clause
        
        query = f"""
            UPDATE users 
            SET {", ".join(update_fields)}
            WHERE email = %s
            RETURNING id
        """
        
        cur.execute(query, update_values)
        updated = cur.fetchone() is not None
        conn.commit()
        return updated
    except Exception as e:
        print(f"Error updating user profile: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def delete_user_account(email, password):
    """Delete user account and all associated data."""
    conn = create_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        
        # Verify password first
        hashed_password = hash_password(password)
        cur.execute(
            "SELECT id FROM users WHERE email = %s AND password = %s",
            (email, hashed_password)
        )
        user = cur.fetchone()
        if not user:
            return False
            
        user_id = user[0]
        
        # Delete associated data
        cur.execute("DELETE FROM transactions WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM predictions WHERE user_id = %s", (user_id,))
        
        # Finally delete user
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting user account: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()