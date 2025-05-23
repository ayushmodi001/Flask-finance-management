# Finance Prediction Model

This directory contains the machine learning components for finance prediction in the RMProject.

## Global Model Approach

The finance prediction system uses a global machine learning model approach that offers several advantages:

1. **Efficient Training**: Instead of training individual models for each user, a single global model is trained on data from all users, significantly reducing computational resources.
2. **Better Generalization**: The global model learns patterns from all users, allowing it to generalize better to new users or users with limited transaction history.
3. **Improved Predictions**: With more data from all users, the model can identify patterns that might not be visible in a single user's transaction history.
4. **Reduced Cold Start Problem**: New users benefit from predictions based on patterns learned from existing users, solving the cold start problem.

## Key Components

- `finance_prediction.py`: Core functionality for training the global model and making predictions
- `train_global_model.py`: Script that can be run to initially train the global model
- `update_global_model.py`: Script for periodically updating the global model with new transaction data

## Model Storage

The global model and its metadata are stored in the following locations:
- Global model: `ml_model/models/global_finance_model.joblib`
- Model metadata: `ml_model/models/global_model_metadata.json`

## How It Works

1. **Data Collection**: Transaction data is collected from all users in the system
2. **Feature Engineering**: The raw transaction data is transformed into features suitable for machine learning
3. **Model Training**: An XGBoost model is trained on the prepared data
4. **Prediction**: When predictions are requested for a specific user, the global model is used with user-specific metrics

## Scheduled Updates

The global model can be updated periodically using the `update_global_model.py` script. This script can be scheduled to run using cron or a similar scheduler:

```
# Example cron job to update the model daily at 2:00 AM
0 2 * * * cd /path/to/RMProject && python ml_model/update_global_model.py >> /path/to/logs/cron.log 2>&1
```

## Fallback Mechanism

The system includes a fallback to user-specific models in case the global model fails to provide accurate predictions for a specific user.

## Compatibility

The global model approach maintains backward compatibility with the existing codebase, ensuring that all functionality continues to work as expected. 