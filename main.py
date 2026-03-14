"""
app.py
------
Flask backend for the Tax Invoice Web Application.
Handles all routes: serving pages, CRUD for customers/products/invoices,
PDF generation, and invoice number auto-increment.
"""
import os
import sqlite3
from flask import Flask, render_template, request, jsonify, Response
from datetime import datetime

# --- TOOLS ---
try:
    from weasyprint import HTML as WeasyHTML
    WEASY_AVAILABLE = True
except Exception:
    WEASY_AVAILABLE = False

try:
    from num2words import num2words
    NUM2WORDS_AVAILABLE = True
except ImportError:
    NUM2WORDS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# ============================================================
# DATABASE & STATES
# ============================================================
INDIAN_STATES = [
    {"name": "Andhra Pradesh", "code": "37"}, {"name": "Karnataka", "code": "29"},
    {"name": "Meghalaya", "code": "17"}, {"name": "Delhi", "code": "07"},
    {"name": "Maharashtra", "code": "27"}, {"name": "Tamil Nadu", "code": "33"}
    # Add more as needed...
]

if not os.path.exists("data"):
    os.makedirs("data")

DB_PATH = os.path.join(os.getcwd(), "data", "invoice_data.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS owner_info (id INTEGER PRIMARY KEY, company_name TEXT, address TEXT, city TEXT, state_name TEXT, state_code TEXT, gstin TEXT, phone TEXT, email TEXT, bank_name TEXT, account_no TEXT, ifsc_code TEXT, branch TEXT, declaration_text TEXT);
        CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, address TEXT, city TEXT, state_name TEXT, state_code TEXT, gstin TEXT, phone TEXT, email TEXT);
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, hsn TEXT, default_price REAL, default_tax REAL, unit TEXT);
        CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_no TEXT, invoice_date TEXT, buyer_name TEXT, subtotal REAL, tax_amount REAL, grand_total REAL);
    """)
    db.commit()
    db.close()

init_db()

def number_to_words(amount):
    try:
        amount = round(float(amount), 2)
        if amount <= 0: return "Indian Rupee Zero Only"
        if NUM2WORDS_AVAILABLE:
            rupees = int(amount)
            paise = int(round((amount - rupees) * 100))
            words = num2words(rupees, lang='en_IN').title()
            if paise > 0:
                paise_words = num2words(paise, lang='en_IN').title()
                return f"Indian Rupee {words} and {paise_words} Paise Only"
            return f"Indian Rupee {words} Only"
        return f"₹ {amount}"
    except: return "Indian Rupee Zero Only"

# ============================================================
# ROUTES (MATCHED TO FRONTEND CALLS)
# ============================================================
@app.route('/')
def index():
    return render_template('invoice.html', states=INDIAN_STATES)

@app.route('/api/customers', methods=['GET', 'POST'])
def handle_customers():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        db.execute("INSERT INTO customers (customer_name, gstin) VALUES (?,?)", (data.get('customer_name'), data.get('gstin')))
        db.commit()
        db.close()
        return jsonify({"status": "success"})
    res = db.execute("SELECT * FROM customers").fetchall()
    db.close()
    return jsonify([dict(row) for row in res])

@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        db.execute("INSERT INTO products (product_name, default_price) VALUES (?,?)", (data.get('product_name'), data.get('default_price')))
        db.commit()
        db.close()
        return jsonify({"status": "success"})
    res = db.execute("SELECT * FROM products").fetchall()
    db.close()
    return jsonify([dict(row) for row in res])

@app.route('/api/owner', methods=['GET', 'POST'])
def handle_owner():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        db.execute("INSERT OR REPLACE INTO owner_info (id, company_name) VALUES (1, ?)", (data.get('company_name'),))
        db.commit()
        db.close()
        return jsonify({"status": "success"})
    owner = db.execute("SELECT * FROM owner_info LIMIT 1").fetchone()
    db.close()
    return jsonify(dict(owner) if owner else {})

@app.route('/api/invoices', methods=['POST'])
def save_invoice():
    data = request.json
    db = get_db()
    cur = db.execute("INSERT INTO invoices (invoice_no, grand_total, tax_amount) VALUES (?,?,?)",
              (data.get('invoice_no'), data.get('grand_total'), data.get('tax_amount')))
    db.commit()
    inv_id = cur.lastrowid
    db.close()
    return jsonify({"status": "success", "invoice_id": inv_id})

@app.route('/api/invoices/<int:inv_id>/pdf')
def generate_pdf(inv_id):
    db = get_db()
    invoice = db.execute("SELECT * FROM invoices WHERE id=?", (inv_id,)).fetchone()
    db.close()
    
    g_words = number_to_words(invoice['grand_total'])
    t_words = number_to_words(invoice['tax_amount'])

    # IMPORTANT: Passing variables for the words
    return render_template('invoice_print.html', invoice=invoice, 
                           grand_total_words=g_words, tax_amount_words=t_words, states=INDIAN_STATES)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)