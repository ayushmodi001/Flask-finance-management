# Finance Management Flask Application

A comprehensive Finance Management web application that helps users track expenses, manage budgets, and predict future spending. Built with **Flask** for the backend and **HTML**, **CSS**, and **JavaScript** for an interactive frontend. The application integrates **XGBoost** machine learning to generate intelligent spending predictions.

---

## 🚀 Features

- **User Authentication:** Secure sign-up and login functionality.
- **Expense Tracking:** Record, edit, and delete daily spending entries.
- **Budget Management:** Define custom monthly or category-wise budgets and monitor progress.
- **Analytics Dashboard:** Intuitive charts and graphs to visualize spending patterns.
- **AI-based Predictions:** XGBoost-powered forecasts of future expenses.
- **Responsive Frontend:** Modern, mobile-friendly UI using HTML, CSS, and JavaScript.
- **Data Export:** Export your financial data to CSV (optional, if implemented).

---

## 🛠 Tech Stack

- **Backend:** [Flask](https://flask.palletsprojects.com/)
- **Frontend:** HTML, CSS, JavaScript (optionally Bootstrap or Chart.js for UI and charts)
- **Machine Learning:** [XGBoost](https://xgboost.readthedocs.io/) (for spending predictions)
- **Database:** SQLite (or your preferred DB)
- **Visualization:** Chart.js or Plotly.js (optional for data visualization)

---


## 📂 Project Structure


---

## ⚡ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/ayushmodi001/RMProject.git
cd RMProject
```

## 🤖 Spending Prediction with XGBoost
- The application uses your historical spending data to train an XGBoost regression model.
- Predictions for next month’s expenses are shown on the dashboard.
- Model retrains on-demand to keep predictions up to date.
