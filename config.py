"""
config.py
---------
Configuration settings for the Tax Invoice application.
Switched to SQLite for simpler cloud deployment.
"""

import os

# ============================================================
# DATABASE CONFIGURATION (SQLite)
# ============================================================

# We define the path for our database file.
# In Railway, we will store this in a persistent volume.
DB_PATH = os.path.join(os.getcwd(), 'invoice_data.db')

# ============================================================
# APPLICATION SETTINGS
# ============================================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
INVOICE_PREFIX = 'INV'