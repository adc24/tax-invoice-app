"""
config.py
---------
Database configuration for the Tax Invoice application.
Update the values below to match your local MySQL setup.
"""

# MySQL database connection settings
DB_CONFIG = {
    'host': 'localhost',        # MySQL server host
    'user': 'root',             # MySQL username
    'password': 'Abhay@123',    # MySQL password — CHANGE THIS
    'database': 'tax_invoice_db', # Database name
    'port': 3306                # MySQL port (default 3306)
}

# Application settings
SECRET_KEY = 'change-this-to-a-random-secret-key'

# Invoice number prefix
INVOICE_PREFIX = 'INV'