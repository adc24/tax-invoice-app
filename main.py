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

# --- CONFIG ---
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
        CREATE TABLE IF NOT EXISTS invoice_items (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, description TEXT, hsn TEXT, quantity REAL, rate REAL, amount REAL);
    """)
    db.commit()
    db.close()

init_db()

# --- THE FIX: Enhanced Number to Words ---
def number_to_words(amount):
    try:
        amount = round(float(amount or 0), 2)
        if amount <= 0: return "Indian Rupee Zero Only"
        
        rupees = int(amount)
        paise = int(round((amount - rupees) * 100))
        
        words = num2words(rupees, lang='en_IN').title()
        result = f"Indian Rupee {words}"
        
        if paise > 0:
            paise_words = num2words(paise, lang='en_IN').title()
            result += f" and {paise_words} Paise"
            
        return result + " Only"
    except Exception as e:
        print(f"Word conversion error: {e}")
        return "Indian Rupee Zero Only"

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('invoice.html', states=INDIAN_STATES)

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

@app.route('/api/invoices', methods=['GET', 'POST'])
def handle_invoices():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        cur = db.execute("INSERT INTO invoices (invoice_no, invoice_date, buyer_name, subtotal, tax_amount, grand_total) VALUES (?,?,?,?,?,?)",
                        (d.get('invoice_no'), datetime.now().strftime('%d-%m-%Y'), d.get('buyer_name'), d.get('subtotal'), d.get('tax_amount'), d.get('grand_total')))
        inv_id = cur.lastrowid
        for item in d.get('items', []):
            db.execute("INSERT INTO invoice_items (invoice_id, description, quantity, rate, amount) VALUES (?,?,?,?,?)",
                       (inv_id, item.get('description'), item.get('quantity'), item.get('rate'), item.get('amount')))
        db.commit()
        return jsonify({"status": "success", "invoice_id": inv_id})
    res = db.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in res])

@app.route('/api/invoices/<int:id>', methods=['DELETE'])
def delete_invoice(id):
    db = get_db()
    db.execute("DELETE FROM invoices WHERE id=?", (id,))
    db.execute("DELETE FROM invoice_items WHERE invoice_id=?", (id,))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/invoices/<int:inv_id>/pdf')
def generate_pdf(inv_id):
    db = get_db()
    invoice = db.execute("SELECT * FROM invoices WHERE id=?", (inv_id,)).fetchone()
    if not invoice:
        return "Invoice Not Found", 404
        
    items = db.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (inv_id,)).fetchall()
    owner = db.execute("SELECT * FROM owner_info LIMIT 1").fetchone()
    
    # CRITICAL FIX: Convert both amounts to words here
    g_words = number_to_words(invoice['grand_total'])
    t_words = number_to_words(invoice['tax_amount'])

    html = render_template('invoice_print.html', 
                           invoice=dict(invoice), 
                           owner=dict(owner) if owner else {}, 
                           items=[dict(i) for i in items], 
                           grand_total_words=g_words, 
                           tax_amount_words=t_words)
    
    if WEASY_AVAILABLE:
        pdf = WeasyHTML(string=html).write_pdf()
        return Response(pdf, mimetype='application/pdf', 
                        headers={'Content-Disposition': f'attachment; filename=Invoice_{invoice["invoice_no"]}.pdf'})
    return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)