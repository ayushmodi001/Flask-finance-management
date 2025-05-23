from database.db_connection import create_db_connection
from ml_model.finance_prediction import predict_and_store, train_global_model
from database.usercrud import get_all_users
import sys
import time

def reset_predictions():
    """Reset the predictions table and force new predictions for all users"""
    print("Resetting predictions table...")
    
    # Connect to database
    conn = create_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    try:
        # First, truncate the predictions table
        cur = conn.cursor()
        cur.execute("DELETE FROM predictions")  # Changed from TRUNCATE to DELETE
        conn.commit()
        print("Predictions table cleared successfully")
        
        # Get all users
        users = get_all_users()
        if not users:
            print("No users found")
            return False
        
        # First, train the global model with all user data
        print("Training global model with all user data...")
        start_time = time.time()
        trained = train_global_model()
        end_time = time.time()
        
        if trained:
            print(f"Global model trained successfully in {end_time - start_time:.2f} seconds")
        else:
            print("Warning: Failed to train global model, will use individual models instead")
        
        # Generate new predictions for each user
        for user in users:
            print(f"Generating new prediction for user {user['id']} ({user.get('email', 'unknown')})")
            predict_and_store(user['id'])
        
        print("All predictions have been reset and regenerated")
        return True
    except Exception as e:
        print(f"Error resetting predictions: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        print("Starting prediction reset process...")
        success = reset_predictions()
        print(f"Process completed with {'success' if success else 'errors'}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1) 