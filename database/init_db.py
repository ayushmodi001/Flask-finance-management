from database.db_connection import create_db_connection

def initialize_database():
    """Initialize all database tables"""
    conn = create_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False

    try:
        cur = conn.cursor()
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                fullname VARCHAR(255) NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                gender VARCHAR(20),
                dob DATE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create transactions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                amount DECIMAL(15,2) NOT NULL,
                transaction_type VARCHAR(10) CHECK (transaction_type IN ('expense', 'income')),
                category VARCHAR(50) NOT NULL,
                description TEXT,
                card_number VARCHAR(16),
                transaction_date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create predictions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            total_income DECIMAL(15,2),
            total_expenses DECIMAL(15,2),
            disposable_income DECIMAL(15,2),
            savings_potential DECIMAL(15,2),
            confidence_score DECIMAL(5,2),
            prediction_period VARCHAR(20),
            occupation VARCHAR(50),  -- Added Occupation column
            city_tier VARCHAR(20),   -- Added City_Tier column
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Add indexes for better performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
            CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);
        """)
        
        conn.commit()
        print("Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()