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

# --- CONFIG & DATABASE ---
INDIAN_STATES = [
    {"name": "Andhra Pradesh", "code": "37"}, {"name": "Karnataka", "code": "29"},
    {"name": "Meghalaya", "code": "17"}, {"name": "Delhi", "code": "07"},
    {"name": "Maharashtra", "code": "27"}, {"name": "Tamil Nadu", "code": "33"}
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
        CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_no TEXT, invoice_date TEXT, buyer_name TEXT, buyer_address TEXT, buyer_city TEXT, buyer_state TEXT, buyer_state_code TEXT, buyer_gstin TEXT, subtotal REAL, tax_amount REAL, grand_total REAL);
        CREATE TABLE IF NOT EXISTS invoice_items (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, sl_no INTEGER, description TEXT, hsn TEXT, quantity REAL, rate REAL, per_unit TEXT, discount_percent REAL, amount REAL, FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE);
    """)
    db.commit()
    db.close()

init_db()

def number_to_words(amount):
    try:
        amount = round(float(amount or 0), 2)
        if amount <= 0: return "Indian Rupee Zero Only"
        rupees = int(amount)
        paise = int(round((amount - rupees) * 100))
        words = num2words(rupees, lang='en_IN').title()
        res = f"Indian Rupee {words}"
        if paise > 0:
            res += f" and {num2words(paise, lang='en_IN').title()} Paise"
        return res + " Only"
    except: return "Indian Rupee Zero Only"

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('invoice.html', states=INDIAN_STATES)

@app.route('/api/number-to-words', methods=['GET'])
def api_words():
    amount = request.args.get('amount', 0)
    return jsonify({"words": number_to_words(amount)})

@app.route('/api/owner', methods=['GET', 'POST'])
def handle_owner():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        db.execute("INSERT OR REPLACE INTO owner_info (id, company_name, gstin, address) VALUES (1,?,?,?)", (d.get('company_name'), d.get('gstin'), d.get('address')))
        db.commit()
        return jsonify({"status": "success"})
    owner = db.execute("SELECT * FROM owner_info LIMIT 1").fetchone()
    return jsonify(dict(owner) if owner else {})

@app.route('/api/customers', methods=['GET', 'POST'])
def handle_customers():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        db.execute("INSERT INTO customers (customer_name, gstin) VALUES (?,?)", (d.get('customer_name'), d.get('gstin')))
        db.commit()
        return jsonify({"status": "success"})
    res = db.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in res])

@app.route('/api/customers/<int:id>', methods=['PUT', 'DELETE'])
def update_customer(id):
    db = get_db()
    if request.method == 'DELETE':
        db.execute("DELETE FROM customers WHERE id=?", (id,))
    else:
        d = request.json
        db.execute("UPDATE customers SET customer_name=?, gstin=? WHERE id=?", (d.get('customer_name'), d.get('gstin'), id))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        db.execute("INSERT INTO products (product_name, default_price) VALUES (?,?)", (d.get('product_name'), d.get('default_price')))
        db.commit()
        return jsonify({"status": "success"})
    res = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in res])

@app.route('/api/products/<int:id>', methods=['PUT', 'DELETE'])
def update_product(id):
    db = get_db()
    if request.method == 'DELETE':
        db.execute("DELETE FROM products WHERE id=?", (id,))
    else:
        d = request.json
        db.execute("UPDATE products SET product_name=?, default_price=? WHERE id=?", (d.get('product_name'), d.get('default_price'), id))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/invoices', methods=['GET', 'POST'])
def handle_invoices():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        cur = db.execute("INSERT INTO invoices (invoice_no, grand_total, buyer_name) VALUES (?,?,?)", (d.get('invoice_no'), d.get('grand_total'), d.get('buyer_name')))
        db.commit()
        return jsonify({"status": "success", "invoice_id": cur.lastrowid})
    res = db.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in res])

@app.route('/api/invoices/<int:id>', methods=['GET', 'DELETE'])
def handle_single_invoice(id):
    db = get_db()
    if request.method == 'DELETE':
        db.execute("DELETE FROM invoices WHERE id=?", (id,))
        db.commit()
        return jsonify({"status": "success"})
    inv = db.execute("SELECT * FROM invoices WHERE id=?", (id,)).fetchone()
    return jsonify(dict(inv))

@app.route('/api/invoices/<int:inv_id>/pdf')
def generate_pdf(inv_id):
    db = get_db()
    invoice = db.execute("SELECT * FROM invoices WHERE id=?", (inv_id,)).fetchone()
    owner = db.execute("SELECT * FROM owner_info LIMIT 1").fetchone()
    g_words = number_to_words(invoice['grand_total'])
    html = render_template('invoice_print.html', invoice=dict(invoice), owner=dict(owner) if owner else {}, grand_total_words=g_words, items=[])
    if WEASY_AVAILABLE:
        pdf = WeasyHTML(string=html).write_pdf()
        return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename=Invoice_{inv_id}.pdf'})
    return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)