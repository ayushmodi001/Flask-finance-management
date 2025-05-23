from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from database.usercrud import signup_user, login_user, get_user_data
from ml_model.finance_prediction import predict_and_store, train_user_model, get_or_train_global_model
from database.finance_crud import (
    store_transaction,
    get_user_transactions,
    get_user_summary,
    store_prediction,
    get_latest_prediction
)
from datetime import datetime, timedelta
import threading
import pandas as pd
import numpy as np
import os
from pathlib import Path
from database.init_db import initialize_database
from decimal import Decimal
from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation 


if not initialize_database():
    print("Failed to initialize database. Exiting...")
    exit(1)

app = Flask(__name__)
app.secret_key = "your_secret_key"

model_ready = False
TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), 'dataset', 'data.csv')

# Initialize the global model at startup
try:
    print("Initializing global finance prediction model...")
    global_model = get_or_train_global_model()
    if global_model:
        print("Global finance prediction model initialized successfully")
        model_ready = True
    else:
        print("Warning: Failed to initialize global model, will use individual models")
        model_ready = True  # Still set to True to allow individual model fallback
except Exception as e:
    print(f"Error initializing global model: {e}")
    model_ready = True  # Still allow app to start and use individual models as fallback





@app.route("/api/check-model-status")
def check_model_status():
    return jsonify({"ready": model_ready})

@app.route("/api/get-predictions")
def get_predictions():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        user_data = get_user_data(session["user"])
        if not user_data:
            return jsonify({"error": "User not found"}), 404

        print(f"Generating predictions for user: {user_data['id']} at {datetime.now()}")
        predict_and_store(user_data["id"])
        prediction = get_latest_prediction(user_data["id"])
        
        # Get user summary to ensure consistent savings potential calculation
        user_summary = get_user_summary(user_data["id"])
        
        if prediction:
            # Calculate base value for forecast - use savings potential as base for more accurate projections
            # This better reflects steady growth in savings over time
            savings_potential = prediction["savings_potential"]
            if user_summary and user_summary["savings_potential"] > 0:
                savings_potential = Decimal(str(user_summary["savings_potential"]))
            elif savings_potential <= 0:
                savings_potential = prediction["total_income"] * Decimal('0.2')
            
            # Calculate disposable income correctly
            disposable_income = prediction["disposable_income"]
            if disposable_income <= 0 and prediction["total_income"] > 0:
                disposable_income = prediction["total_income"] * Decimal('0.3')  # Assume 30% is disposable if not specified
            
            # Create more realistic forecast that shows accumulation of savings over time
            # Month 1: Current disposable income
            # Subsequent months: Previous month + savings potential (monthly savings added to balance)
            forecast_values = []
            current_value = disposable_income
            forecast_values.append(str(current_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)))
            
            # Each month adds the monthly savings potential to the previous month's value
            for _ in range(5):  # For the next 5 months
                current_value += savings_potential
                forecast_values.append(str(current_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)))
            
            return jsonify({
                "predictions": {
                    "total_income": str(prediction["total_income"]),
                    "total_expenses": str(prediction["total_expenses"]),
                    "disposable_income": str(prediction["disposable_income"]),
                    "savings_potential": str(savings_potential),
                    "confidence_score": str(prediction["confidence_score"]),
                    "prediction_period": prediction["prediction_period"],
                    "last_updated": prediction["created_at"],
                    "forecast_data": {
                        "labels": ["Current", "+1 Month", "+2 Months", "+3 Months", "+4 Months", "+5 Months"],
                        "values": forecast_values
                    }
                }
            })
        else:
            # Return default values if no prediction is available
            # Get current income from user_summary if available
            default_income = Decimal('0.00')
            if user_summary and user_summary["income"] > 0:
                default_income = Decimal(str(user_summary["income"]))
                
            default_savings = default_income * Decimal('0.2')  # 20% of income
            default_disposable = default_income * Decimal('0.3')  # 30% of income
            
            # Create forecast values that show accumulation of savings over time
            default_forecast_values = []
            current_value = default_disposable
            default_forecast_values.append(str(current_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)))
            
            # Each month adds the monthly savings to the previous month's value
            for _ in range(5):  # For the next 5 months
                current_value += default_savings
                default_forecast_values.append(str(current_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)))
            
            return jsonify({
                "predictions": {
                    "total_income": str(default_income),
                    "total_expenses": str(default_income * Decimal('0.7')),  # 70% of income
                    "disposable_income": str(default_disposable),
                    "savings_potential": str(default_savings),
                    "confidence_score": "0.00",
                    "prediction_period": "Monthly",
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "forecast_data": {
                        "labels": ["Current", "+1 Month", "+2 Months", "+3 Months", "+4 Months", "+5 Months"],
                        "values": default_forecast_values
                    }
                }
            })
    except Exception as e:
        print(f"Error in get_predictions: {e}")
        # Fallback values
        fallback_income = Decimal('0.00')
        fallback_expenses = Decimal('0.00')
        fallback_disposable = Decimal('0.00')
        fallback_savings = Decimal('0.00')  # 20% of 5000.00
        
        # Generate forecast with savings accumulation
        fallback_forecast = []
        current_value = fallback_disposable
        fallback_forecast.append(str(current_value))
        
        for _ in range(5):
            current_value += fallback_savings
            fallback_forecast.append(str(current_value))
            
        return jsonify({
            "predictions": {
                "total_income": "0.00",
                "total_expenses": "0.00",
                "disposable_income": "0.00",
                "savings_potential": "0.00",  # 20% of 5000.00
                "confidence_score": "0.00",
                "prediction_period": "Monthly",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "forecast_data": {
                    "labels": ["Current", "+1 Month", "+2 Months", "+3 Months", "+4 Months", "+5 Months"],
                    "values": fallback_forecast
                }
            }
        })

@app.route("/api/financial-summary")
def get_financial_summary():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        user_data = get_user_data(session["user"])
        if not user_data:
            return jsonify({"error": "User not found"}), 404

        summary = get_user_summary(user_data["id"])
        if not summary:
            return jsonify({
                "income": 0,
                "income_trend": 0,
                "expenses": 0,
                "expenses_trend": 0,
                "disposable_income": 0,
                "disposable_trend": 0,
                "savings_potential": 0
            })
        
        return jsonify({
            "income": float(summary["income"]),
            "income_trend": float(summary["income_trend"]),
            "expenses": float(summary["expenses"]),
            "expenses_trend": float(summary["expenses_trend"]),
            "disposable_income": float(summary["disposable_income"]),
            "disposable_trend": float(summary["disposable_trend"]),
            "savings_potential": float(summary["savings_potential"])
        })
    except Exception as e:
        print(f"Error getting user summary: {e}")
        return jsonify({"error": "Failed to fetch summary"}), 500

@app.route("/api/transactions")
def get_transactions():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        user_data = get_user_data(session["user"])
        if not user_data:
            return jsonify({"error": "User not found"}), 404

        transactions = get_user_transactions(user_data["id"])
        return jsonify(transactions)
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return jsonify({"error": "Failed to fetch transactions"}), 500


@app.route("/api/spending-trend")
def get_spending_trend():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    time_range = request.args.get('range', 'month')
    user_data = get_user_data(session["user"])
    
    if not user_data:
        return jsonify({"error": "User not found"}), 404

    # Calculate date range
    end_date = datetime.now()
    if time_range == 'week':
        start_date = end_date - timedelta(days=7)
    elif time_range == 'month':
        start_date = end_date - timedelta(days=30)
    elif time_range == 'quarter':
        start_date = end_date - timedelta(days=90)
    else:  # year
        start_date = end_date - timedelta(days=365)

    # Get transactions for the period
    transactions = get_user_transactions(user_data["id"], start_date, end_date)
    
    # Process transactions into daily totals
    daily_data = {}
    for transaction in transactions:
        # Check if transaction_date is already a string or datetime object
        if isinstance(transaction['transaction_date'], str):
            date = transaction['transaction_date']  # Already a string, use as is
        else:
            date = transaction['transaction_date'].strftime('%Y-%m-%d')  # Convert datetime to string
            
        if date not in daily_data:
            daily_data[date] = {'income': 0, 'expenses': 0}
        
        if transaction['transaction_type'] == 'income':
            daily_data[date]['income'] += float(transaction['amount'])
        else:
            daily_data[date]['expenses'] += float(transaction['amount'])

    # Sort by date and format for chart
    dates = sorted(daily_data.keys())
    
    return jsonify({
        'labels': dates,
        'income': [daily_data[date]['income'] for date in dates],
        'expenses': [daily_data[date]['expenses'] for date in dates]
    })

@app.route("/api/expense-breakdown")
def get_expense_breakdown():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    time_range = request.args.get('range', 'month')
    user_data = get_user_data(session["user"])
    
    if not user_data:
        return jsonify({"error": "User not found"}), 404

    # Calculate date range
    end_date = datetime.now()
    if time_range == 'month':
        start_date = end_date - timedelta(days=30)
    elif time_range == 'quarter':
        start_date = end_date - timedelta(days=90)
    else:  # year
        start_date = end_date - timedelta(days=365)

    # Get transactions
    transactions = get_user_transactions(user_data["id"], start_date, end_date)
    
    # Calculate category totals for expenses only
    categories = {}
    for transaction in transactions:
        if transaction['transaction_type'] == 'expense':
            category = transaction['category']
            if category not in categories:
                categories[category] = 0
            categories[category] += float(transaction['amount'])

    # Calculate percentages
    total = sum(categories.values()) or 1  # Avoid division by zero
    category_percentages = {k: (v/total)*100 for k, v in categories.items()}

    return jsonify({
        'categories': list(categories.keys()),
        'values': list(category_percentages.values())
    })

@app.route("/api/spending-analysis")
def get_spending_analysis():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_data = get_user_data(session["user"])
    if not user_data:
        return jsonify({"error": "User not found"}), 404

    # Get transactions for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    transactions = get_user_transactions(user_data["id"], start_date, end_date)

    # If no transactions, provide default response
    if not transactions:
        return jsonify({
            'insights': [
                {
                    'message': "No transactions found in the last 30 days. Add transactions to see spending insights.",
                    'type': 'info'
                }
            ],
            'categories': [],
            'values': []
        })

    # Calculate insights
    expense_transactions = [t for t in transactions if t['transaction_type'] == 'expense']
    total_spending = sum(float(t['amount']) for t in expense_transactions)
    
    # Calculate category spending
    categories = {}
    for transaction in expense_transactions:
        category = transaction['category']
        if category not in categories:
            categories[category] = 0
        categories[category] += float(transaction['amount'])
    
    # Generate insights
    insights = []
    
    # 1. Highest spending category
    if categories:
        # Sort categories by spending
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        highest_category = sorted_categories[0]
        highest_percent = (highest_category[1] / total_spending) * 100 if total_spending > 0 else 0
        
        insights.append({
            'message': f"Your highest spending category is {highest_category[0]} at ₹{formatCurrency(highest_category[1])} ({highest_percent:.1f}% of total)",
            'type': 'category'
        })
        
        # 2. If we have enough categories, provide more insights
        if len(sorted_categories) >= 3:
            top_three_total = sum(cat[1] for cat in sorted_categories[:3])
            top_three_percent = (top_three_total / total_spending) * 100 if total_spending > 0 else 0
            
            if top_three_percent > 75:
                insights.append({
                    'message': f"Your top 3 categories account for {top_three_percent:.1f}% of your spending. Consider diversifying your budget.",
                    'type': 'distribution'
                })
    
    # 3. Day of week analysis if we have enough transactions
    if len(expense_transactions) >= 5:
        day_spending = {}
        for transaction in expense_transactions:
            try:
                # Parse the transaction date
                if isinstance(transaction['transaction_date'], str):
                    date = datetime.strptime(transaction['transaction_date'].split()[0], '%Y-%m-%d')
                else:
                    date = transaction['transaction_date']
                
                day_name = date.strftime('%A')  # Get day name (Monday, Tuesday, etc)
                if day_name not in day_spending:
                    day_spending[day_name] = 0
                day_spending[day_name] += float(transaction['amount'])
            except Exception as e:
                print(f"Error parsing date: {e}")
                continue
        
        if day_spending:
            highest_day = max(day_spending.items(), key=lambda x: x[1])
            insights.append({
                'message': f"You spend the most on {highest_day[0]}s (₹{formatCurrency(highest_day[1])}).",
                'type': 'timing'
            })
    
    # 4. General spending insight
    avg_daily_spending = total_spending / 30
    insights.append({
        'message': f"Your average daily spending is ₹{formatCurrency(avg_daily_spending)}.",
        'type': 'general'
    })

    return jsonify({
        'insights': insights,
        'categories': list(categories.keys()),
        'values': list(categories.values())
    })

@app.route("/api/budget-recommendations")
def get_budget_recommendations():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_data = get_user_data(session["user"])
    if not user_data:
        return jsonify({"error": "User not found"}), 404

    # Get recent transactions
    transactions = get_user_transactions(user_data["id"])
    
    # Calculate basic recommendations
    total_income = sum(float(t['amount']) for t in transactions if t['transaction_type'] == 'income')
    total_expenses = sum(float(t['amount']) for t in transactions if t['transaction_type'] == 'expense')
    
    # If no transactions, provide default values
    if not transactions:
        return jsonify({
            'recommendations': [
                {
                    'text': "Start tracking your expenses to get personalized budget recommendations.",
                    'type': 'info'
                },
                {
                    'text': "Try to save at least 20% of your income each month.",
                    'type': 'general'
                }
            ],
            'total_income': 0,
            'total_expenses': 0
        })
    
    # Generate recommendations
    recommendations = []
    
    # 1. Check expense to income ratio
    expense_ratio = total_expenses / total_income if total_income > 0 else 0
    if expense_ratio > 0.9:
        recommendations.append({
            'text': "Your expenses are over 90% of your income. This is a critical situation that requires immediate attention.",
            'potential_savings': total_expenses - (0.7 * total_income),
            'type': 'critical'
        })
    elif expense_ratio > 0.7:
        recommendations.append({
            'text': "Your expenses are over 70% of your income. Consider reducing non-essential spending.",
            'potential_savings': total_expenses - (0.7 * total_income),
            'type': 'warning'
        })
    
    # 2. Category-specific recommendations
    categories = {}
    for transaction in transactions:
        if transaction['transaction_type'] == 'expense':
            category = transaction['category']
            if category not in categories:
                categories[category] = 0
            categories[category] += float(transaction['amount'])
    
    # Find highest spending category
    if categories:
        highest_category = max(categories.items(), key=lambda x: x[1])
        category_percent = (highest_category[1] / total_expenses) * 100 if total_expenses > 0 else 0
        
        if category_percent > 40:
            recommendations.append({
                'text': f"Your {highest_category[0]} expenses make up {category_percent:.1f}% of your total spending. Consider ways to reduce this category.",
                'potential_savings': highest_category[1] * 0.2,  # Suggest saving 20% in this category
                'type': 'category'
            })
    
    # 3. General recommendation if none specific
    if not recommendations:
        # If doing well, recommend savings increase
        savings_ratio = 1 - expense_ratio
        if savings_ratio > 0.3:
            recommendations.append({
                'text': f"You're saving {savings_ratio*100:.1f}% of your income. Great job! Consider investing some of your savings for better returns.",
                'type': 'positive'
            })
        else:
            recommendations.append({
                'text': "Try to increase your savings to at least 20% of your income.",
                'type': 'general'
            })
    
    return jsonify({
        'recommendations': recommendations,
        'total_income': total_income,
        'total_expenses': total_expenses
    })

def formatCurrency(amount):
    return "{:.2f}".format(amount)
@app.route("/")
def homedirect():
    return redirect("/dashboard")

@app.route("/signupform", methods=["GET"])
def signup_page():
    return render_template("signupform.html")

@app.route("/loginform", methods=["GET"])
def login_page():
    return render_template("loginform.html")

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(force=True)  # Ensure JSON parsing

    if not data:
        return jsonify({"error": "Invalid request, expected JSON"}), 400

    fullname = data.get("fullname")
    username = data.get("username")
    email = data.get("email")
    phone = data.get("phone")
    gender = data.get("gender")
    dob = data.get("dob")
    password = data.get("password")

    if signup_user(fullname, username, email, phone, gender, dob, password):
        return jsonify({"message": "Signup successful!", "redirect": "/loginform"}), 201
    else:
        return jsonify({"error": "Signup failed!"}), 500

@app.route("/login", methods=["POST"])
def login():
    # Handle both JSON & form data
    if request.content_type == "application/json":
        data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required!"}), 400

    if login_user(email, password):
        session["user"] = email
        return jsonify({"message": "Login successful!", "redirect": "/dashboard"}), 200
    else:
        return jsonify({"error": "Invalid credentials!"}), 401

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", user=session["user"], model_ready=model_ready)    
    return redirect(url_for("login_page"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/loginform")




@app.route("/check-session")
def check_session():
    return jsonify({"authenticated": "user" in session})

@app.route('/payment', methods=['GET', 'POST'])
def add_transaction():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    print(f"Current user in session: {session['user']}")
        
    if request.method == 'POST':
        try:
            user_email = session["user"]
            print(f"Fetching user data for email: {user_email}")
            
            user_data = get_user_data(user_email)
            if not user_data:
                return jsonify({
                    "error": "User not found",
                    "details": f"No data found for email: {user_email}"
                }), 404

            # Get form data
            transaction_data = {
                'user_id': user_data['id'],
                'amount': float(request.form['amount']),
                'transaction_type': request.form['transaction_type'],
                'category': request.form['category'],
                'description': request.form['description'],
                'card_number': request.form['card_number']
            }

            # Store transaction using the renamed function
            transaction_id = store_transaction(transaction_data)
            
            if transaction_id:
                if model_ready:
                    # Only try prediction if model is ready
                    try:
                        predict_and_store(user_data['id'])
                    except Exception as e:
                        print(f"Prediction error (non-critical): {e}")
                
                return jsonify({
                    "message": "Transaction added successfully",
                    "transaction_id": transaction_id,
                    "redirect": "/dashboard"
                }), 200
                    
            return jsonify({
                "error": "Error adding transaction"
            }), 500
        
        except Exception as e:
            print(f"Error in add_transaction route: {str(e)}")
            return jsonify({
                "error": str(e)
            }), 500
    
    # GET request - render the payment form
    return render_template("payment_form.html", user=session["user"])

if __name__ == "__main__":
    app.run(debug=True)