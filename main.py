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

# --- PDF & WORDS TOOLS ---
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
# DATABASE HELPER (Volume-Friendly Path)
# ============================================================
# Create a 'data' folder if it doesn't exist to house the SQLite file
if not os.path.exists("data"):
    os.makedirs("data")

# Path must point inside the 'data' folder for the volume to work correctly
DB_PATH = os.path.join(os.getcwd(), "data", "invoice_data.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS owner_info (id INTEGER PRIMARY KEY, company_name TEXT, address TEXT, city TEXT, state_name TEXT, state_code TEXT, gstin TEXT, phone TEXT, email TEXT, bank_name TEXT, account_no TEXT, ifsc_code TEXT, branch TEXT, declaration_text TEXT);
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, hsn TEXT, default_price REAL, default_tax REAL, unit TEXT);
        CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_no TEXT, invoice_date TEXT, buyer_name TEXT, buyer_address TEXT, buyer_city TEXT, buyer_state TEXT, buyer_state_code TEXT, buyer_gstin TEXT, subtotal REAL, tax_amount REAL, grand_total REAL);
        CREATE TABLE IF NOT EXISTS invoice_items (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, description TEXT, hsn TEXT, quantity REAL, rate REAL, amount REAL);
    """)
    db.commit()
    db.close()

init_db()

# ============================================================
# FIXED: NUMBER TO WORDS
# ============================================================
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
# ROUTES
# ============================================================
@app.route('/')
def index():
    return render_template('invoice.html')

@app.route('/api/owner', methods=['GET', 'POST'])
def handle_owner():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        existing = db.execute("SELECT id FROM owner_info LIMIT 1").fetchone()
        if existing:
            db.execute("UPDATE owner_info SET company_name=?", (data.get('company_name'),))
        else:
            db.execute("INSERT INTO owner_info (company_name) VALUES (?)", (data.get('company_name'),))
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
    cur = db.execute("INSERT INTO invoices (invoice_no, subtotal, tax_amount, grand_total) VALUES (?,?,?,?)",
              (data.get('invoice_no'), data.get('subtotal'), data.get('tax_amount'), data.get('grand_total')))
    db.commit()
    inv_id = cur.lastrowid
    db.close()
    return jsonify({"status": "success", "invoice_id": inv_id})

@app.route('/api/invoices/<int:inv_id>/pdf')
def generate_pdf(inv_id):
    db = get_db()
    invoice = db.execute("SELECT * FROM invoices WHERE id=?", (inv_id,)).fetchone()
    owner = db.execute("SELECT * FROM owner_info LIMIT 1").fetchone()
    db.close()
    
    g_words = number_to_words(invoice['grand_total'])
    t_words = number_to_words(invoice['tax_amount'])

    html = render_template('invoice_print.html', invoice=invoice, owner=owner, 
                           items=[], grand_total_words=g_words, tax_amount_words=t_words)
    if WEASY_AVAILABLE:
        return Response(WeasyHTML(string=html).write_pdf(), mimetype='application/pdf')
    return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)