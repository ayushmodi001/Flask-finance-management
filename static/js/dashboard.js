// Constants for transaction categories
const EXPENSE_CATEGORIES = {
    'Groceries': '🛒',
    'Transport': '🚗',
    'Eating_Out': '🍽️',
    'Entertainment': '🎬',
    'Utilities': '💡',
    'Healthcare': '⚕️',
    'Education': '📚',
    'Miscellaneous': '📦',
    'Rent': '🏠',
    'Loan_Repayment': '💰',
    'Insurance': '🛡️'
};

const INCOME_CATEGORIES = {
    'Salary': '💵',
    'Bonus': '🎁',
    'Investment': '📈',
    'Other': '💼'
};

// Initialize all event listeners and dashboard components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const toggleBtn = document.getElementById('toggleSidebar');
    const hamburgerMenu = document.getElementById('hamburgerMenu');
    const avatarContainer = document.getElementById('avatar-container');
    const avatarMenu = document.getElementById('avatar-menu');
    const logoutBtn = document.getElementById('logout-btn');

    // Initialize sidebar state
    const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isSidebarCollapsed) {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
        hamburgerMenu.style.opacity = '1';
    } else {
        hamburgerMenu.style.opacity = '0';
    }

    // Event Listeners
    toggleBtn?.addEventListener('click', () => {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
        hamburgerMenu.style.opacity = '1';
        localStorage.setItem('sidebarCollapsed', 'true');
    });

    hamburgerMenu?.addEventListener('click', () => {
        sidebar.classList.remove('collapsed');
        mainContent.classList.remove('expanded');
        hamburgerMenu.style.opacity = '0';
        localStorage.setItem('sidebarCollapsed', 'false');
    });

    avatarContainer?.addEventListener('click', (e) => {
        e.stopPropagation();
        avatarMenu?.classList.toggle('active');
    });

    document.addEventListener('click', () => {
        avatarMenu?.classList.contains('active') && avatarMenu.classList.remove('active');
    });

    logoutBtn?.addEventListener('click', () => window.location.href = '/logout');

    // Chart range selectors
    document.getElementById('timeRange')?.addEventListener('change', (e) => {
        fetchSpendingTrend(e.target.value);
    });

    document.getElementById('expenseTimeRange')?.addEventListener('change', (e) => {
        fetchExpenseBreakdown(e.target.value);
    });

    // Initialize Dashboard or Payment Form based on current page
    if (window.location.pathname === '/dashboard') {
        initializeDashboard();
    } else if (window.location.pathname === '/payment') {
        initializePaymentForm();
    }
});

// Payment Form Functions
function initializePaymentForm() {
    const form = document.getElementById('payment-form');
    const transactionTypeSelect = document.getElementById('transaction_type');

    if (transactionTypeSelect) {
        transactionTypeSelect.addEventListener('change', handleTransactionTypeChange);
        // Initialize form state based on default selection
        handleTransactionTypeChange({ target: transactionTypeSelect });
    }

    if (form) {
        form.addEventListener('submit', handlePaymentSubmit);
    }
}

function handleTransactionTypeChange(event) {
    const transactionType = event.target.value;
    const categorySelect = document.getElementById('category');
    const cardNumberField = document.getElementById('card-number-field');
    const descriptionField = document.getElementById('description-field');

    if (!categorySelect) return;

    // Clear existing options
    categorySelect.innerHTML = '';

    if (transactionType === 'income') {
        // Show only income categories
        Object.entries(INCOME_CATEGORIES).forEach(([category, icon]) => {
            const option = new Option(`${icon} ${category}`, category);
            categorySelect.add(option);
        });

        // Hide card number and simplify description for income
        if (cardNumberField) cardNumberField.style.display = 'none';
        if (descriptionField) {
            const descriptionInput = descriptionField.querySelector('input, textarea');
            if (descriptionInput) {
                descriptionInput.placeholder = 'Source of income (optional)';
            }
        }
    } else {
        // Show expense categories
        Object.entries(EXPENSE_CATEGORIES).forEach(([category, icon]) => {
            const option = new Option(`${icon} ${category}`, category);
            categorySelect.add(option);
        });

        // Show card number and update description placeholder
        if (cardNumberField) cardNumberField.style.display = 'block';
        if (descriptionField) {
            const descriptionInput = descriptionField.querySelector('input, textarea');
            if (descriptionInput) {
                descriptionInput.placeholder = 'Description (optional)';
            }
        }
    }
}

async function handlePaymentSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    try {
        submitButton.disabled = true;
        submitButton.textContent = 'Processing...';

        const formData = new FormData(form);
        const response = await fetch('/payment', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            alert('Transaction added successfully!');
        } else {
            throw new Error(data.error || 'Failed to add transaction');
        }
    } catch (error) {
        alert(error.message);
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Submit Transaction';
    }
}

// Main dashboard initialization
function initializeDashboard() {
    // Call these functions in sequence to avoid race conditions
    fetchFinancialSummary()
        .then(() => {
            // Only fetch predictions after financial summary is loaded
            fetchMLPredictions();
        });
    
    // These can still run concurrently
    fetchTransactions('all');
    fetchSpendingAnalysis();
    fetchBudgetRecommendations();
    initializeAllCharts();
}

// Financial Summary Functions
async function fetchFinancialSummary() {
    try {
        const response = await fetch('/api/financial-summary');
        if (!response.ok) throw new Error('Failed to fetch financial summary');
        const data = await response.json();
        updateFinancialSummary(data);
        return data; // Return data for chaining
    } catch (error) {
        console.error('Error:', error);
        updateFinancialSummary({
            income: 0,
            income_trend: 0,
            expenses: 0,
            expenses_trend: 0,
            disposable_income: 0,
            disposable_trend: 0,
            savings_potential: 0
        });
        return null;
    }
}

function updateFinancialSummary(data) {
    const formatAmount = (amount) => formatCurrency(amount || 0);
    const formatTrend = (trend) => (trend || 0).toFixed(1);

    document.getElementById('income-amount').textContent = formatAmount(data.income);
    document.getElementById('income-trend').textContent = formatTrend(data.income_trend);
    
    document.getElementById('expense-amount').textContent = formatAmount(data.expenses);
    document.getElementById('expense-trend').textContent = formatTrend(data.expenses_trend);
    
    document.getElementById('disposable-amount').textContent = formatAmount(data.disposable_income);
    document.getElementById('disposable-trend').textContent = formatTrend(data.disposable_trend);
    
    // Use innerHTML instead of textContent to add the percentage indicator
    const potentialAmount = document.getElementById('potential-amount');
    if (potentialAmount) {
        potentialAmount.innerHTML = `${formatAmount(data.savings_potential)} <span class="percentage">(20% of income)</span>`;
    }
}

// Transaction Functions
async function fetchTransactions(filter = 'all') {
    const transactionsList = document.getElementById('transactionsList');
    if (!transactionsList) return;

    transactionsList.innerHTML = `
        <div class="loading-transactions">
            <div class="loading-spinner"></div>
            <p>Loading transactions...</p>
        </div>`;

    try {
        const response = await fetch('/api/transactions');
        if (!response.ok) throw new Error('Failed to fetch transactions');
        const transactions = await response.json();

        if (!transactions || transactions.length === 0) {
            transactionsList.innerHTML = `
                <div class="no-transactions">
                    <p>No transactions found</p>
                    <a href="/payment" class="add-transaction-btn">Add Your First Transaction</a>
                </div>`;
            return;
        }

        const filteredTransactions = filter === 'all' 
            ? transactions 
            : transactions.filter(t => filter === 'income' ? !t.is_expense : t.is_expense);

        renderTransactions(filteredTransactions);
    } catch (error) {
        console.error('Error:', error);
        transactionsList.innerHTML = `
            <div class="error-transactions">
                <p>Failed to load transactions</p>
                <button onclick="fetchTransactions()" class="retry-btn">Try Again</button>
            </div>`;
    }
}

function renderTransactions(transactions) {
    const transactionsList = document.getElementById('transactionsList');
    
    const categoryIcons = {
        'Groceries': '🛒',
        'Transport': '🚗',
        'Eating_Out': '🍽️',
        'Entertainment': '🎬',
        'Utilities': '💡',
        'Healthcare': '⚕️',
        'Education': '📚',
        'Miscellaneous': '📦',
        'Rent': '🏠',
        'Loan_Repayment': '💰',
        'Insurance': '🛡️',
        'Salary': '💵',
        'Bonus': '🎁',
        'Investment': '📈'
    };

    const transactionsHTML = transactions.map(transaction => {
        const icon = categoryIcons[transaction.category] || '💼';
        const date = new Date(transaction.transaction_date).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short'
        });
        const isExpense = transaction.transaction_type === 'expense';
        const amountClass = isExpense ? 'expense' : 'income';
        const amountPrefix = isExpense ? '-' : '+';

        return `
            <div class="transaction-item">
                <div class="transaction-icon" title="${transaction.category}">${icon}</div>
                <div class="transaction-info">
                    <div class="transaction-header">
                        <h4>${transaction.description || transaction.category}</h4>
                        <span class="transaction-amount ${amountClass}">
                            ${amountPrefix} ₹${formatCurrency(transaction.amount)}
                        </span>
                    </div>
                    <div class="transaction-details">
                        <span>${transaction.category}</span>
                        <span>•</span>
                        <span>${date}</span>
                        <span>•</span>
                        <span>${transaction.payment_method || 'Card'}</span>
                    </div>
                </div>
            </div>`;
    }).join('');

    transactionsList.innerHTML = transactionsHTML;
}

// ML Prediction Functions
async function fetchMLPredictions() {
    const predictionElements = {
        score: document.getElementById('confidence-score'),
        period: document.getElementById('prediction-period'),
        updated: document.getElementById('last-updated'),
        amount: document.getElementById('potential-amount')
    };

    // Check if we already have a significant savings potential value displayed
    const currentPotentialAmount = predictionElements.amount?.textContent || '';
    const currentAmountValue = parseFloat(currentPotentialAmount.replace(/[^\d.]/g, '')) || 0;
    const isSignificantAmount = currentAmountValue > 5000; // Don't overwrite if we already have a high value
    
    if (!isSignificantAmount) {
        Object.values(predictionElements).forEach(el => {
            if (el) el.innerHTML = '<span class="loading">Loading...</span>';
        });
    }

    try {
        const response = await fetch('/api/get-predictions');
        if (!response.ok) throw new Error('Failed to fetch predictions');
        
        const data = await response.json();
        if (!data.predictions) throw new Error('No prediction data available');

        // Only update if we don't already have a significant value
        if (!isSignificantAmount) {
            updatePredictionDisplays(data.predictions);
        } else {
            console.log("Skipping prediction update because we already have a significant amount:", currentAmountValue);
            // Still update other elements except the amount
            if (predictionElements.score) {
                predictionElements.score.textContent = `${parseFloat(data.predictions.confidence_score || 85).toFixed(1)}%`;
            }
            if (predictionElements.period) {
                predictionElements.period.textContent = data.predictions.prediction_period || 'Monthly';
            }
            if (predictionElements.updated) {
                try {
                    predictionElements.updated.textContent = formatDateTime(new Date(data.predictions.last_updated));
                } catch (e) {
                    predictionElements.updated.textContent = 'Just now';
                }
            }
            
            // Update the forecast chart
            if (data.predictions.forecast_data) {
                updateForecastChart(data.predictions.forecast_data);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (!isSignificantAmount) {
            Object.values(predictionElements).forEach(el => {
                if (el) el.innerHTML = '<span class="error">Failed to load</span>';
            });
        }
    }
}

function updatePredictionDisplays(data) {
    try {
        // Debug logging to see what's happening
        console.log("Updating prediction displays with data:", {
            savingsPotential: data.savings_potential,
            totalIncome: data.total_income
        });
        
        // Update the savings potential amount
        const potentialAmount = document.getElementById('potential-amount');
        if (potentialAmount) {
            // Show savings potential as both amount and percentage of income
            const savingsAmount = parseFloat(data.savings_potential) || 0;
            
            // Always display 20% since that's our fixed savings percentage
            potentialAmount.innerHTML = `${formatCurrency(savingsAmount)} <span class="percentage">(20% of income)</span>`;
        }
        
        // Update the confidence score
        const confidenceScore = document.getElementById('confidence-score');
        if (confidenceScore) {
            confidenceScore.textContent = `${parseFloat(data.confidence_score || 85).toFixed(1)}%`;
        }
        
        // Update the prediction period
        const predictionPeriod = document.getElementById('prediction-period');
        if (predictionPeriod) {
            predictionPeriod.textContent = data.prediction_period || 'Monthly';
        }
        
        // Update the last updated timestamp
        const lastUpdated = document.getElementById('last-updated');
        if (lastUpdated) {
            try {
                lastUpdated.textContent = formatDateTime(new Date(data.last_updated));
            } catch (e) {
                lastUpdated.textContent = 'Just now';
                console.error('Error formatting date:', e);
            }
        }

        // Update the forecast chart if data is available
        if (data.forecast_data && data.forecast_data.labels && data.forecast_data.values) {
            updateForecastChart(data.forecast_data);
        } else {
            // Create default forecast data if not available
            const defaultValue = parseFloat(data.disposable_income) || 0;
            const defaultForecast = {
                labels: ["Current", "+1 Month", "+2 Months", "+3 Months", "+4 Months", "+5 Months"],
                values: [
                    defaultValue.toString(),
                    (defaultValue * 1.1).toString(),
                    (defaultValue * 1.15).toString(),
                    (defaultValue * 1.2).toString(),
                    (defaultValue * 1.25).toString(),
                    (defaultValue * 1.3).toString()
                ]
            };
            updateForecastChart(defaultForecast);
        }
    } catch (error) {
        console.error('Error updating prediction displays:', error);
    }
}

// New function to fetch spending analysis
async function fetchSpendingAnalysis() {
    try {
        const response = await fetch('/api/spending-analysis');
        if (!response.ok) throw new Error('Failed to fetch spending analysis');
        
        const data = await response.json();
        displaySpendingInsights(data);
    } catch (error) {
        console.error('Error fetching spending analysis:', error);
        displaySpendingInsights({ insights: [], categories: [], values: [] });
    }
}

// New function to display spending insights
function displaySpendingInsights(data) {
    const insightsContainer = document.getElementById('spendingInsights');
    if (!insightsContainer) return;
    
    if (data.insights && data.insights.length > 0) {
        const insightsHTML = data.insights.map(insight => `
            <div class="insight-item" data-type="${insight.type || 'general'}">
                <p>${insight.message}</p>
            </div>
        `).join('');
        insightsContainer.innerHTML = insightsHTML;
    } else {
        insightsContainer.innerHTML = `
            <div class="no-data">
                <p>Not enough data to generate insights yet.</p>
            </div>
        `;
    }
    
    // If we have categories, initialize the category comparison chart
    if (data.categories && data.categories.length > 0) {
        initializeCategoryComparisonChart(data.categories, data.values);
    }
}

// New function to initialize category comparison chart
function initializeCategoryComparisonChart(categories, values) {
    const ctx = document.getElementById('categoryComparisonChart')?.getContext('2d');
    if (!ctx) return;
    
    const existingChart = Chart.getChart('categoryComparisonChart');
    if (existingChart) {
        existingChart.destroy();
    }
    
    const colors = [
        '#6366f1', '#10b981', '#f59e0b', '#ec4899', 
        '#8b5cf6', '#64748b', '#0ea5e9', '#d946ef'
    ];
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Spending Amount',
                data: values,
                backgroundColor: categories.map((_, i) => colors[i % colors.length])
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '₹' + formatCurrency(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => '₹' + formatCurrencyShort(value)
                    }
                },
                x: {
                    ticks: {
                        autoSkip: true,
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// New function to fetch budget recommendations
async function fetchBudgetRecommendations() {
    try {
        const response = await fetch('/api/budget-recommendations');
        if (!response.ok) throw new Error('Failed to fetch budget recommendations');
        
        const data = await response.json();
        displayBudgetRecommendations(data);
    } catch (error) {
        console.error('Error fetching budget recommendations:', error);
        displayBudgetRecommendations({ recommendations: [], total_income: 0, total_expenses: 0 });
    }
}

// New function to display budget recommendations
function displayBudgetRecommendations(data) {
    const recommendationsContainer = document.getElementById('budgetRecommendations');
    if (!recommendationsContainer) return;
    
    if (data.recommendations && data.recommendations.length > 0) {
        const recommendationsHTML = data.recommendations.map(rec => `
            <div class="recommendation-item" data-type="${rec.type || 'general'}">
                <p>${rec.text}</p>
                ${rec.potential_savings ? `<p class="savings-amount">Potential savings: ₹${formatCurrency(rec.potential_savings)}</p>` : ''}
            </div>
        `).join('');
        recommendationsContainer.innerHTML = recommendationsHTML;
    } else {
        recommendationsContainer.innerHTML = `
            <div class="no-data">
                <p>Your budget looks good! No specific recommendations at this time.</p>
            </div>
        `;
    }
    
    // Initialize budget optimization chart
    initializeBudgetOptimizationChart(data.total_income, data.total_expenses);
}

// New function to initialize budget optimization chart
function initializeBudgetOptimizationChart(income, expenses) {
    const ctx = document.getElementById('budgetOptimizationChart')?.getContext('2d');
    if (!ctx) return;
    
    const existingChart = Chart.getChart('budgetOptimizationChart');
    if (existingChart) {
        existingChart.destroy();
    }
    
    const idealExpenseRatio = 0.7; // 70% of income
    const idealExpenses = income * idealExpenseRatio;
    const isOverBudget = expenses > idealExpenses;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Current Budget', 'Ideal Budget'],
            datasets: [
                {
                    label: 'Income',
                    data: [income, income],
                    backgroundColor: '#10b981'
                },
                {
                    label: 'Expenses',
                    data: [expenses, idealExpenses],
                    backgroundColor: isOverBudget ? '#ef4444' : '#6366f1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: false,
                    ticks: {
                        callback: value => '₹' + formatCurrencyShort(value)
                    }
                },
                x: {
                    stacked: false
                }
            }
        }
    });
}

// Chart Functions
function initializeAllCharts() {
    initializeSpendingTrendChart();
    initializeExpenseDonutChart();
    initializeForecastChart();
    fetchSpendingTrend('month');
    fetchExpenseBreakdown('month');
}

async function fetchSpendingTrend(timeRange) {
    try {
        const response = await fetch(`/api/spending-trend?range=${timeRange}`);
        if (!response.ok) throw new Error('Failed to fetch spending trend');
        const data = await response.json();
        updateSpendingTrendChart(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

async function fetchExpenseBreakdown(timeRange) {
    try {
        const response = await fetch(`/api/expense-breakdown?range=${timeRange}`);
        if (!response.ok) throw new Error('Failed to fetch expense breakdown');
        const data = await response.json();
        updateExpenseDonutChart(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

// Chart Initialization Functions
function initializeSpendingTrendChart() {
    const ctx = document.getElementById('spendingTrendChart')?.getContext('2d');
    if (!ctx) return;

    const existingChart = Chart.getChart('spendingTrendChart');
    if (existingChart) {
        existingChart.destroy();
    }
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Income',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }, {
                label: 'Expenses',
                data: [],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => '₹' + formatCurrencyShort(value)
                    }
                }
            }
        }
    });
}

function initializeExpenseDonutChart() {
    const ctx = document.getElementById('expenseDonutChart')?.getContext('2d');
    if (!ctx) return;

    const existingChart = Chart.getChart('expenseDonutChart');
    if (existingChart) {
        existingChart.destroy();
    }
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#6366f1',
                    '#10b981',
                    '#f59e0b',
                    '#ec4899',
                    '#8b5cf6',
                    '#64748b'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%'
        }
    });
}

function initializeForecastChart() {
    const ctx = document.getElementById('forecastChart')?.getContext('2d');
    if (!ctx) return;

    const existingChart = Chart.getChart('forecastChart');
    if (existingChart) {
        existingChart.destroy();
    }
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.3)');
    gradient.addColorStop(1, 'rgba(139, 92, 246, 0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Current', '+1 Month', '+2 Months', '+3 Months', '+4 Months', '+5 Months'],
            datasets: [{
                label: 'Predicted Amount',
                data: [],
                borderColor: '#8b5cf6',
                backgroundColor: gradient,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => '₹' + formatCurrencyShort(value)
                    }
                }
            }
        }
    });
}

// Utility Functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        maximumFractionDigits: 0
    }).format(value);
}

function formatCurrencyShort(value) {
    if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
    if (value >= 1000) return (value / 1000).toFixed(1) + 'k';
    return value;
}

function formatDateTime(date) {
    return date.toLocaleString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Chart Update Functions
function updateSpendingTrendChart(data) {
    const chart = Chart.getChart('spendingTrendChart');
    if (chart) {
        chart.data.labels = data.labels;
        chart.data.datasets[0].data = data.income;
        chart.data.datasets[1].data = data.expenses;
        chart.update();
    }
}

function updateExpenseDonutChart(data) {
    const chart = Chart.getChart('expenseDonutChart');
    if (chart) {
        chart.data.labels = data.categories;
        chart.data.datasets[0].data = data.values;
        chart.update();
    }
}

function updateForecastChart(data) {
    const chart = Chart.getChart('forecastChart');
    if (chart) {
        chart.data.labels = data.labels;
        chart.data.datasets[0].data = data.values;
        chart.update();
    }
}