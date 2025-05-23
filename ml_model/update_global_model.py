#!/usr/bin/env python3
"""
Global Model Update Script

This script updates the global finance prediction model by training it
on the latest transaction data from all users. It can be scheduled to run
periodically (e.g., daily, weekly) using cron or a similar scheduler.

Usage:
    python update_global_model.py
"""

import os
import sys
import logging
import time
from datetime import datetime

# Add the parent directory to the Python path to enable relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_model.finance_prediction import train_global_model
from database.db_connection import create_db_connection
from database.usercrud import get_all_users

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, 'global_model_updates.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def update_global_model():
    """Update the global finance prediction model with the latest data"""
    logging.info("Starting global model update process")
    
    # Verify database connection
    conn = create_db_connection()
    if not conn:
        logging.error("Failed to connect to database")
        return False
    conn.close()
    
    # Verify we have enough users/data to train
    users = get_all_users()
    if not users:
        logging.warning("No users found in the system. Skipping model update.")
        return False
        
    logging.info(f"Found {len(users)} users in the system. Proceeding with model update.")
    
    # Train the global model
    start_time = time.time()
    try:
        success = train_global_model()
        end_time = time.time()
        
        if success:
            logging.info(f"Global model updated successfully in {end_time - start_time:.2f} seconds")
            return True
        else:
            logging.error("Failed to update global model")
            return False
            
    except Exception as e:
        logging.error(f"Error updating global model: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logging.info(f"=== GLOBAL MODEL UPDATE JOB STARTED AT {datetime.now()} ===")
        success = update_global_model()
        logging.info(f"=== GLOBAL MODEL UPDATE JOB COMPLETED: {'SUCCESS' if success else 'FAILED'} ===")
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Unexpected error in update_global_model.py: {str(e)}")
        sys.exit(1) 