# Database connection settings
DB_HOST = "localhost"
DB_NAME = "personal_finance"
DB_USER = "postgres"
DB_PASS = "Ayush0407"
SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
