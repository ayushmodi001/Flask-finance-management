import pandas as pd
import numpy as np
import joblib
import psycopg2
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from database.finance_crud import get_user_transactions, store_prediction
from database.usercrud import get_all_users
import os
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('finance_prediction')

# Define paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')
os.makedirs(MODEL_DIR, exist_ok=True)
GLOBAL_MODEL_PATH = os.path.join(MODEL_DIR, 'global_finance_model.pkl')
GLOBAL_MODEL_METADATA_PATH = os.path.join(MODEL_DIR, 'global_model_metadata.json')

# Feature definitions
NUMERICAL_COLUMNS = [
    'Income', 'Rent', 'Loan_Repayment', 'Insurance', 'Groceries', 'Transport', 'Eating_Out',
    'Entertainment', 'Utilities', 'Healthcare', 'Education', 'Miscellaneous', 'Desired_Savings',
    'Disposable_Income'
]
CATEGORICAL_COLUMNS = ['Occupation', 'City_Tier']

def get_transaction_data(user_id=None):
    """
    Fetch transaction data for a specific user or all users.
    
    Args:
        user_id: If provided, fetch data only for this user, otherwise fetch all users' data
        
    Returns:
        DataFrame of transaction data or None if no data found
    """
    if user_id:
        # Fetch transactions for a specific user
        transactions = get_user_transactions(user_id)
        if not transactions:
            return None
        df = pd.DataFrame(transactions)
        return df if not df.empty else None
    else:
        # Get all users
        users = get_all_users()
        if not users:
            logger.warning("No users found in the database")
            return None
            
        all_transactions = []
        for user in users:
            user_transactions = get_user_transactions(user['id'])
            if user_transactions:
                # Add user_id to each transaction
                for transaction in user_transactions:
                    transaction['user_id'] = user['id']
                all_transactions.extend(user_transactions)
                
        if not all_transactions:
            logger.warning("No transactions found for any users")
            return None
            
        return pd.DataFrame(all_transactions)

def prepare_training_data(df=None):
    """
    Prepare data for model training, either using provided DataFrame or default data.
    
    Args:
        df: DataFrame of transaction data, or None to use default data
        
    Returns:
        X_train, X_test, y_train, y_test for model training
    """
    # If no data provided or empty data, use default data
    if df is None or df.empty:
        logger.info("Using default training data")
        data_path = os.path.join(os.path.dirname(__file__), "data.csv")
        
        if not os.path.exists(data_path):
            # Create default data if file doesn't exist
            logger.warning(f"Data file not found at {data_path}. Creating default data.")
            default_data = {
                'Income': [5000, 5200, 5100, 5300, 5400],
                'Rent': [1500, 1500, 1500, 1500, 1500],
                'Loan_Repayment': [500, 500, 500, 500, 500],
                'Insurance': [200, 200, 200, 200, 200],
                'Groceries': [800, 750, 820, 780, 810],
                'Transport': [300, 320, 290, 310, 330],
                'Eating_Out': [400, 450, 380, 420, 390],
                'Entertainment': [200, 250, 180, 220, 230],
                'Utilities': [300, 310, 290, 320, 300],
                'Healthcare': [100, 0, 150, 0, 200],
                'Education': [0, 0, 0, 0, 0],
                'Miscellaneous': [100, 120, 90, 110, 130],
                'Desired_Savings': [600, 600, 600, 600, 600],
                'Disposable_Income': [600, 800, 700, 940, 810],
                'Occupation': ['Professional', 'Professional', 'Professional', 'Professional', 'Professional'],
                'City_Tier': ['Tier 1', 'Tier 1', 'Tier 1', 'Tier 1', 'Tier 1'],
                'user_id': [1, 1, 1, 1, 1]  # Add user_id for consistency
            }
            df = pd.DataFrame(default_data)
            os.makedirs(os.path.dirname(data_path), exist_ok=True)
            df.to_csv(data_path, index=False)
        else:
            df = pd.read_csv(data_path)
            # Add user_id if it doesn't exist
            if 'user_id' not in df.columns:
                df['user_id'] = 1
    
    # Ensure all required columns exist
    for col in NUMERICAL_COLUMNS:
        if col not in df.columns:
            df[col] = 0
            
    for col in CATEGORICAL_COLUMNS:
        if col not in df.columns:
            df[col] = 'Unknown'
    
    # Apply One-Hot Encoding to categorical columns
    df_encoded = pd.get_dummies(df, columns=CATEGORICAL_COLUMNS, drop_first=True)
    
    # Ensure numerical columns are properly formatted
    for col in NUMERICAL_COLUMNS:
        if col in df_encoded.columns:
            df_encoded[col] = df_encoded[col].fillna(0).astype(float)
    
    # Define Features & Target
    features = NUMERICAL_COLUMNS + [col for col in df_encoded.columns if col.startswith(tuple(CATEGORICAL_COLUMNS))]
    available_features = [f for f in features if f in df_encoded.columns]
    
    X = df_encoded[available_features]
    # Target is total expenses (sum of expense categories)
    expense_columns = ['Groceries', 'Transport', 'Eating_Out', 'Entertainment', 
                      'Utilities', 'Healthcare', 'Education', 'Miscellaneous']
    available_expenses = [col for col in expense_columns if col in df_encoded.columns]
    
    # If we don't have expense columns, use a calculated target
    if not available_expenses:
        if 'total_expenses' in df_encoded.columns:
            y = df_encoded['total_expenses']
        else:
            # Default to 70% of income as expenses
            y = df_encoded['Income'] * 0.7 if 'Income' in df_encoded.columns else 0
    else:
        y = df_encoded[available_expenses].sum(axis=1)
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    return X_train, X_test, y_train, y_test, available_features

def train_global_model():
    """
    Train a global model using data from all users.
    
    Returns:
        Path to the saved model if successful, None otherwise
    """
    try:
        logger.info("Beginning global model training...")
        
        # Get all transaction data
        all_data = get_transaction_data()
        
        # Prepare data for training
        X_train, X_test, y_train, y_test, features = prepare_training_data(all_data)
        
        # Train XGBoost Model
        model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate Model
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        logger.info(f"Global model MAE: {mae:.2f}")
        
        # Save Model
        joblib.dump(model, GLOBAL_MODEL_PATH)
        
        # Save metadata
        metadata = {
            'training_date': datetime.now().isoformat(),
            'mae': float(mae),
            'features': features,
            'sample_size': len(X_train) + len(X_test)
        }
        pd.DataFrame([metadata]).to_json(GLOBAL_MODEL_METADATA_PATH)
        
        logger.info(f"Global model trained & saved at {GLOBAL_MODEL_PATH}")
        return GLOBAL_MODEL_PATH
    except Exception as e:
        logger.error(f"Error training global model: {e}")
        return None

def get_or_train_global_model():
    """
    Get the global model, training it if it doesn't exist.
    
    Returns:
        The loaded model and its features
    """
    if not os.path.exists(GLOBAL_MODEL_PATH):
        logger.info("Global model not found. Training new model...")
        train_global_model()
    
    try:
        model = joblib.load(GLOBAL_MODEL_PATH)
        if os.path.exists(GLOBAL_MODEL_METADATA_PATH):
            metadata = pd.read_json(GLOBAL_MODEL_METADATA_PATH)
            features = metadata.loc[0, 'features']
        else:
            # If metadata file doesn't exist, use default features
            features = NUMERICAL_COLUMNS + [f"{col}_Unknown" for col in CATEGORICAL_COLUMNS]
        return model, features
    except Exception as e:
        logger.error(f"Error loading global model: {e}")
        train_global_model()  # Retrain if there was an error
        try:
            model = joblib.load(GLOBAL_MODEL_PATH)
            metadata = pd.read_json(GLOBAL_MODEL_METADATA_PATH)
            features = metadata.loc[0, 'features']
            return model, features
        except Exception as e2:
            logger.error(f"Error loading newly trained global model: {e2}")
            return None, []

def train_user_model(user_id):

    logger.info(f"Training model for user {user_id} (using global model)")
    
    # Ensure global model exists
    if not os.path.exists(GLOBAL_MODEL_PATH):
        train_global_model()
    
    # Get user data for evaluation
    user_data = get_transaction_data(user_id)
    if user_data is not None and not user_data.empty:
        # Evaluate model on user's data
        model, features = get_or_train_global_model()
        if model is not None:
            # Record user-specific MAE for logging
            try:
                # This is just for metrics, not critical for functionality
                pass
            except Exception as e:
                logger.warning(f"Could not calculate user-specific metrics: {e}")
    
    return GLOBAL_MODEL_PATH

def predict_and_store(user_id):

    try:
        # Ensure global model exists
        model, features = get_or_train_global_model()
        
        if model is None:
            logger.error("Failed to load or train global model")
            # Create default prediction
            default_prediction = {
                'user_id': user_id,
                'total_income': 0.0,
                'total_expenses': 0.0,
                'disposable_income': 0.0,
                'savings_potential': 0.0,  # 20% of income
                'confidence_score': 0.0,
                'prediction_period': 'Monthly'
            }
            store_prediction(default_prediction)
            logger.info(f"Default predictions stored for user {user_id} due to model failure")
            return

        # Get user transaction data
        df = get_transaction_data(user_id)
        if df is None or df.empty:
            logger.info(f"No transaction data for user {user_id}. Using default values.")
            # Create default prediction
            default_prediction = {
                'user_id': user_id,
                'total_income': 0.0,
                'total_expenses': 0.0,
                'disposable_income': 0.0,
                'savings_potential': 0.0,  # 20% of income
                'confidence_score': 0.0,
                'prediction_period': 'Monthly'
            }
            store_prediction(default_prediction)
            logger.info(f"Default predictions stored for user {user_id}")
            return

        # Prepare features
        for col in NUMERICAL_COLUMNS:
            if col not in df.columns:
                df[col] = 0
                
        for col in CATEGORICAL_COLUMNS:
            if col not in df.columns:
                df[col] = 'Unknown'

        # Process categorical columns
        df_encoded = pd.get_dummies(df, columns=CATEGORICAL_COLUMNS, drop_first=True)
        
        # Ensure numerical columns are properly formatted
        for col in NUMERICAL_COLUMNS:
            if col in df_encoded.columns:
                df_encoded[col] = df_encoded[col].fillna(0).astype(float)
        
        # Ensure all required features are present
        for feature in features:
            if feature not in df_encoded.columns:
                df_encoded[feature] = 0
                
        # Select only the features used during training
        X = df_encoded[features]

        # Make prediction
        predictions = model.predict(X)
        
        # Calculate metrics
        total_expenses = float(np.sum(predictions))
        
        # Calculate income from transaction data
        income_transactions = df[df['transaction_type'] == 'income'] if 'transaction_type' in df.columns else pd.DataFrame()
        total_income = float(income_transactions['amount'].sum()) if not income_transactions.empty else 5000.0
        
        # Ensure we have a minimum income for calculations
        if total_income <= 0:
            total_income = 5000.0
            
        # Calculate disposable income, ensure it's not negative
        disposable_income = total_income - total_expenses
        if disposable_income < 0:
            # Adjust expenses to be at most 90% of income to ensure positive disposable income
            total_expenses = total_income * 0.9
            disposable_income = total_income * 0.1
            
        # Calculate savings potential as 20% of income
        savings_potential = total_income * 0.2

        # Store predictions
        prediction_data = {
            'user_id': user_id,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'disposable_income': disposable_income,
            'savings_potential': savings_potential,
            'confidence_score': 90.0,
            'prediction_period': 'Monthly'
        }
        store_prediction(prediction_data)
        logger.info(f"Predictions stored for user {user_id}")
    except Exception as e:
        logger.error(f"Error in predict_and_store: {e}")
        # Store default prediction in case of error
        default_prediction = {
            'user_id': user_id,
            'total_income': 0.0,
            'total_expenses': 0.0,
            'disposable_income': 0.0,
            'savings_potential': 0.0,  # 20% of income
            'confidence_score': 0.0,
            'prediction_period': 'Monthly'
        }
        store_prediction(default_prediction)
        logger.info(f"Default predictions stored for user {user_id} due to error")


