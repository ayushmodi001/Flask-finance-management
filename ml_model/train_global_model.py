import os
import sys
import logging
from datetime import datetime

# Add parent directory to path to allow importing from ml_model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_model.finance_prediction import train_global_model
from database.usercrud import get_all_users
from database.db_connection import create_db_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'global_model_training.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('train_global_model')

def main():
    """
    Train the global finance prediction model using all available user data.
    This script should be run as a scheduled task (e.g., daily or weekly).
    """
    try:
        logger.info("=" * 50)
        logger.info("Starting global model training process")
        
        # Check database connection
        conn = create_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        conn.close()
        
        # Get all users to check if we have enough data
        users = get_all_users()
        if not users:
            logger.warning("No users found in database. Cannot train model.")
            return False
            
        logger.info(f"Found {len(users)} users in the database")
        
        # Train the global model
        start_time = datetime.now()
        model_path = train_global_model()
        end_time = datetime.now()
        
        if model_path:
            training_time = (end_time - start_time).total_seconds()
            logger.info(f"Global model trained successfully in {training_time:.2f} seconds")
            logger.info(f"Model saved to: {model_path}")
            return True
        else:
            logger.error("Failed to train global model")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error during global model training: {e}")
        return False
        
    finally:
        logger.info("Global model training process completed")
        logger.info("=" * 50)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 