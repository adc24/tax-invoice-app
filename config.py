"""
config.py
---------
Configuration settings for the Tax Invoice application.
Includes Database connection parameters and app secrets.
"""

import os
from urllib.parse import urlparse

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

# Check if Railway has provided a MYSQL_URL
railway_db_url = os.environ.get('MYSQL_URL')

if railway_db_url:
    # Parse the Railway URL into components
    url = urlparse(railway_db_url)
    DB_CONFIG = {
        'host': url.hostname,
        'user': url.username,
        'password': url.password,
        'database': url.path[1:],  # Removes the leading slash
        'port': url.port or 3306
    }
else:
    # Fallback to LOCAL development settings
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'Abhay@123',
        'database': 'tax_invoice_db',
        'port': 3306
    }

# ============================================================
# APPLICATION SETTINGS
# ============================================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
INVOICE_PREFIX = 'INV'