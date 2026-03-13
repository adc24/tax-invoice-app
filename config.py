"""
config.py
---------
Configuration settings for the Tax Invoice application.
Includes Database connection parameters and app secrets.
"""

import os

# ============================================================
# DATABASE CONFIGURATION
# ============================================================
# These values are used for LOCAL development.
# In Production (Render/Railway), set these as Environment Variables.
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Abhay@123',  # Change this to your local password
    'database': 'tax_invoice_db',             # Change this to your local DB name
    'port': 3306
}

# ============================================================
# APPLICATION SETTINGS
# ============================================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
INVOICE_PREFIX = 'INV'