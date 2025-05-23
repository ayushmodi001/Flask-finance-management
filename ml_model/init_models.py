

import os
import sys
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_model.finance_prediction import get_or_train_global_model

def create_directories():
    """Create necessary directories for models and logs"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create models directory
    models_dir = os.path.join(base_dir, 'ml_model', 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Create logs directory
    logs_dir = os.path.join(base_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    return models_dir, logs_dir

def init_logging(logs_dir):
    """Initialize logging"""
    log_file = os.path.join(logs_dir, 'model_initialization.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def initialize_models():
    """Initialize all necessary models"""
    try:
        # Initialize global finance model
        logging.info("Initializing global finance prediction model...")
        model = get_or_train_global_model()
        
        if model:
            logging.info("Global finance prediction model initialized successfully")
            return True
        else:
            logging.warning("Failed to initialize global model")
            return False
    except Exception as e:
        logging.error(f"Error initializing models: {str(e)}")
        return False

if __name__ == "__main__":
    models_dir, logs_dir = create_directories()
    
    init_logging(logs_dir)
    
    logging.info(f"=== MODEL INITIALIZATION STARTED AT {datetime.now()} ===")
    
    success = initialize_models()
    
    logging.info(f"=== MODEL INITIALIZATION COMPLETED: {'SUCCESS' if success else 'FAILED'} ===")
    
    sys.exit(0 if success else 1) 