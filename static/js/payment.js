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

document.addEventListener('DOMContentLoaded', () => {
    initializePaymentForm();
});

function initializePaymentForm() {
    const form = document.getElementById('payment-form');
    const transactionTypeSelect = document.getElementById('transaction_type');
    const paymentMethodSelect = document.getElementById('payment_method');

    if (transactionTypeSelect) {
        transactionTypeSelect.addEventListener('change', handleTransactionTypeChange);
        handleTransactionTypeChange({ target: transactionTypeSelect });
    }

    if (paymentMethodSelect) {
        paymentMethodSelect.addEventListener('change', handlePaymentMethodChange);
        handlePaymentMethodChange({ target: paymentMethodSelect });
    }

    if (form) {
        form.addEventListener('submit', handlePaymentSubmit);
    }
}

function handleTransactionTypeChange(event) {
    const transactionType = event.target.value;
    const categorySelect = document.getElementById('category');
    const descriptionField = document.getElementById('description-field');

    categorySelect.innerHTML = '';

    if (transactionType === 'income') {
        Object.entries(INCOME_CATEGORIES).forEach(([category, icon]) => {
            const option = new Option(`${icon} ${category}`, category);
            categorySelect.add(option);
        });
        descriptionField.querySelector('input').placeholder = 'Source of income (optional)';
    } else {
        Object.entries(EXPENSE_CATEGORIES).forEach(([category, icon]) => {
            const option = new Option(`${icon} ${category}`, category);
            categorySelect.add(option);
        });
        descriptionField.querySelector('input').placeholder = 'Description (optional)';
    }
}

function handlePaymentMethodChange(event) {
    const paymentMethod = event.target.value;
    const cardNumberField = document.getElementById('card-number-field');
    const bankAccountField = document.getElementById('bank-account-field');
    const upiField = document.getElementById('upi-field');

    if (paymentMethod === 'card') {
        cardNumberField.style.display = 'block';
        bankAccountField.style.display = 'none';
        upiField.style.display = 'none';
    } else if (paymentMethod === 'bank') {
        cardNumberField.style.display = 'none';
        bankAccountField.style.display = 'block';
        upiField.style.display = 'none';
    } else if (paymentMethod === 'upi') {
        cardNumberField.style.display = 'none';
        bankAccountField.style.display = 'none';
        upiField.style.display = 'block';
    } else {
        cardNumberField.style.display = 'none';
        bankAccountField.style.display = 'none';
        upiField.style.display = 'none';
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