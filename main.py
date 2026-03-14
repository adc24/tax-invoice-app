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
# DATABASE & CONFIG
# ============================================================
INDIAN_STATES = [
    {"name": "Andhra Pradesh", "code": "37"}, {"name": "Arunachal Pradesh", "code": "12"},
    {"name": "Assam", "code": "18"}, {"name": "Bihar", "code": "10"},
    {"name": "Chhattisgarh", "code": "22"}, {"name": "Delhi", "code": "07"},
    {"name": "Goa", "code": "30"}, {"name": "Gujarat", "code": "24"},
    {"name": "Haryana", "code": "06"}, {"name": "Himachal Pradesh", "code": "02"},
    {"name": "Jharkhand", "code": "20"}, {"name": "Karnataka", "code": "29"},
    {"name": "Kerala", "code": "32"}, {"name": "Madhya Pradesh", "code": "23"},
    {"name": "Maharashtra", "code": "27"}, {"name": "Manipur", "code": "14"},
    {"name": "Meghalaya", "code": "17"}, {"name": "Mizoram", "code": "15"},
    {"name": "Nagaland", "code": "13"}, {"name": "Odisha", "code": "21"},
    {"name": "Punjab", "code": "03"}, {"name": "Rajasthan", "code": "08"},
    {"name": "Sikkim", "code": "11"}, {"name": "Tamil Nadu", "code": "33"},
    {"name": "Telangana", "code": "36"}, {"name": "Tripura", "code": "16"},
    {"name": "Uttar Pradesh", "code": "09"}, {"name": "Uttarakhand", "code": "05"},
    {"name": "West Bengal", "code": "19"}
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
        CREATE TABLE IF NOT EXISTS invoice_items (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, description TEXT, hsn TEXT, quantity REAL, rate REAL, amount REAL);
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
# MAIN ROUTES
# ============================================================
@app.route('/')
def index():
    return render_template('invoice.html', states=INDIAN_STATES)

# ============================================================
# CUSTOMER API (Full CRUD)
# ============================================================
@app.route('/api/customers', methods=['GET', 'POST'])
def api_customers():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        db.execute("INSERT INTO customers (customer_name, address, city, state_name, state_code, gstin, phone, email) VALUES (?,?,?,?,?,?,?,?)",
                   (data.get('customer_name'), data.get('address'), data.get('city'), data.get('state_name'), data.get('state_code'), data.get('gstin'), data.get('phone'), data.get('email')))
        db.commit()
        db.close()
        return jsonify({"status": "success"})
    customers = db.execute("SELECT * FROM customers ORDER BY customer_name").fetchall()
    db.close()
    return jsonify([dict(row) for row in customers])

@app.route('/api/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    db = get_db()
    db.execute("DELETE FROM customers WHERE id=?", (id,))
    db.commit()
    db.close()
    return jsonify({"status": "success"})

# ============================================================
# PRODUCT API (Full CRUD)
# ============================================================
@app.route('/api/products', methods=['GET', 'POST'])
def api_products():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        db.execute("INSERT INTO products (product_name, hsn, default_price, default_tax, unit) VALUES (?,?,?,?,?)",
                   (data.get('product_name'), data.get('hsn'), data.get('default_price'), data.get('default_tax'), data.get('unit')))
        db.commit()
        db.close()
        return jsonify({"status": "success"})
    products = db.execute("SELECT * FROM products ORDER BY product_name").fetchall()
    db.close()
    return jsonify([dict(row) for row in products])

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (id,))
    db.commit()
    db.close()
    return jsonify({"status": "success"})

# ============================================================
# OWNER API
# ============================================================
@app.route('/api/owner', methods=['GET', 'POST'])
def handle_owner():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        db.execute("""INSERT OR REPLACE INTO owner_info 
                   (id, company_name, address, city, state_name, state_code, gstin, phone, email, bank_name, account_no, ifsc_code, branch, declaration_text) 
                   VALUES (1,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (data.get('company_name'), data.get('address'), data.get('city'), data.get('state_name'), data.get('state_code'), data.get('gstin'), data.get('phone'), data.get('email'), data.get('bank_name'), data.get('account_no'), data.get('ifsc_code'), data.get('branch'), data.get('declaration_text')))
        db.commit()
        db.close()
        return jsonify({"status": "success"})
    owner = db.execute("SELECT * FROM owner_info LIMIT 1").fetchone()
    db.close()
    return jsonify(dict(owner) if owner else {})

# ============================================================
# INVOICE API
# ============================================================
@app.route('/api/invoices', methods=['GET', 'POST'])
def api_invoices():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        cur = db.execute("INSERT INTO invoices (invoice_no, invoice_date, buyer_name, subtotal, tax_amount, grand_total) VALUES (?,?,?,?,?,?)",
                  (data.get('invoice_no'), datetime.now().strftime('%Y-%m-%d %H:%M'), data.get('buyer_name'), data.get('subtotal'), data.get('tax_amount'), data.get('grand_total')))
        inv_id = cur.lastrowid
        # Save line items
        for item in data.get('items', []):
            db.execute("INSERT INTO invoice_items (invoice_id, description, hsn, quantity, rate, amount) VALUES (?,?,?,?,?,?)",
                       (inv_id, item.get('description'), item.get('hsn'), item.get('quantity'), item.get('rate'), item.get('amount')))
        db.commit()
        db.close()
        return jsonify({"status": "success", "invoice_id": inv_id})
    
    invoices = db.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
    db.close()
    return jsonify([dict(row) for row in invoices])

# ============================================================
# PDF GENERATION
# ============================================================
@app.route('/api/invoices/<int:inv_id>/pdf')
def generate_pdf(inv_id):
    db = get_db()
    invoice = db.execute("SELECT * FROM invoices WHERE id=?", (inv_id,)).fetchone()
    if not invoice:
        db.close()
        return "Invoice Not Found", 404
        
    items = db.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (inv_id,)).fetchall()
    owner = db.execute("SELECT * FROM owner_info LIMIT 1").fetchone()
    db.close()
    
    g_words = number_to_words(invoice['grand_total'])
    t_words = number_to_words(invoice['tax_amount'])

    html = render_template('invoice_print.html', 
                           invoice=dict(invoice), 
                           owner=dict(owner) if owner else {}, 
                           items=[dict(i) for i in items], 
                           grand_total_words=g_words, 
                           tax_amount_words=t_words, 
                           states=INDIAN_STATES)
    
    if WEASY_AVAILABLE:
        pdf = WeasyHTML(string=html, base_url=request.url_root).write_pdf()
        return Response(pdf, mimetype='application/pdf', 
                        headers={'Content-Disposition': f'attachment; filename=Invoice_{invoice["invoice_no"]}.pdf'})
    return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)