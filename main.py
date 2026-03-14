"""
app.py
------
Flask backend for the Tax Invoice Web Application.
Handles all routes: serving pages, CRUD for customers/products/invoices,
PDF generation, and invoice number auto-increment.
"""
"""
app.py
------
Flask backend for the Tax Invoice Web Application.
SQLite Version with Fixed Tax-to-Words logic.
"""

import os
import sqlite3
from flask import Flask, render_template, request, jsonify, Response
from datetime import datetime
import json

# --- SAFE IMPORT WRAPPER ---
try:
    from weasyprint import HTML as WeasyHTML
    WEASY_AVAILABLE = True
    print("SUCCESS: WeasyPrint loaded successfully.")
except Exception as e:
    WEASY_AVAILABLE = False
    print(f"CRITICAL: WeasyPrint failed to load. PDF features disabled. Error: {e}")

try:
    from num2words import num2words
    NUM2WORDS_AVAILABLE = True
except ImportError:
    NUM2WORDS_AVAILABLE = False
# ---------------------------

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# ============================================================
# DATABASE HELPER (SQLite Version - Easy to Connect)
# ============================================================
DB_PATH = "invoice_data.db"

def get_db():
    """Create and return a SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS owner_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT, address TEXT, city TEXT, state_name TEXT,
            state_code TEXT, gstin TEXT, phone TEXT, email TEXT,
            bank_name TEXT, account_no TEXT, ifsc_code TEXT, branch TEXT,
            declaration_text TEXT
        );
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT, address TEXT, city TEXT, state_name TEXT,
            state_code TEXT, gstin TEXT, phone TEXT, email TEXT
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT, hsn TEXT, default_price REAL, default_tax REAL, unit TEXT
        );
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT, invoice_date TEXT,
            buyer_name TEXT, buyer_address TEXT, buyer_city TEXT, buyer_state TEXT,
            buyer_state_code TEXT, buyer_gstin TEXT, buyer_phone TEXT,
            ship_to_name TEXT, ship_to_address TEXT, ship_to_city TEXT,
            ship_to_state TEXT, ship_to_state_code TEXT, ship_to_gstin TEXT,
            delivery_note TEXT, payment_mode TEXT, reference_no TEXT,
            other_references TEXT, buyer_order_no TEXT, buyer_order_date TEXT,
            dispatch_doc_no TEXT, delivery_note_date TEXT,
            dispatched_through TEXT, destination TEXT, terms_of_delivery TEXT,
            tax_type TEXT, custom_tax_rate REAL,
            subtotal REAL, tax_amount REAL, grand_total REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER, sl_no INTEGER, description TEXT, hsn TEXT,
            quantity REAL, rate REAL, per_unit TEXT, discount_percent REAL, amount REAL,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        );
        CREATE TABLE IF NOT EXISTS invoice_counter (
            id INTEGER PRIMARY KEY, prefix TEXT, last_number INTEGER
        );
    """)
    db.commit()
    db.close()

# Run initialization on startup
init_db()

# ============================================================
# FIXED: NUMBER TO WORDS CONVERSION (Handles Tax properly)
# ============================================================
def number_to_words(amount):
    """Convert amount to Indian Rupee words format."""
    try:
        amount = round(float(amount), 2)  # Critical: Round to 2 decimal places
        if amount <= 0:
            return "Indian Rupee Zero Only"
            
        if NUM2WORDS_AVAILABLE:
            rupees = int(amount)
            # This logic extracts the decimal part as whole paise
            paise = int(round((amount - rupees) * 100))
            
            words = num2words(rupees, lang='en_IN').title()
            if paise > 0:
                paise_words = num2words(paise, lang='en_IN').title()
                return f"Indian Rupee {words} and {paise_words} Paise Only"
            return f"Indian Rupee {words} Only"
        return f"₹ {amount} Only"
    except Exception as e:
        print(f"Error in words conversion: {e}")
        return "Indian Rupee Zero Only"

# ============================================================
# INDIAN STATES LIST
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
    {"name": "West Bengal", "code": "19"}, {"name": "Jammu & Kashmir", "code": "01"},
    {"name": "Ladakh", "code": "38"}, {"name": "Chandigarh", "code": "04"},
    {"name": "Puducherry", "code": "34"}, {"name": "Lakshadweep", "code": "31"},
    {"name": "Andaman & Nicobar Islands", "code": "35"},
    {"name": "Dadra & Nagar Haveli and Daman & Diu", "code": "26"},
]

# ============================================================
# ROUTES — PAGES
# ============================================================
@app.route('/')
def index():
    return render_template('invoice.html', states=INDIAN_STATES)

# ============================================================
# ROUTES — OWNER INFO
# ============================================================
@app.route('/api/owner', methods=['GET'])
def get_owner():
    db = get_db()
    owner = db.execute("SELECT * FROM owner_info LIMIT 1").fetchone()
    db.close()
    return jsonify(dict(owner) if owner else {})

@app.route('/api/owner', methods=['POST'])
def update_owner():
    data = request.json
    db = get_db()
    existing = db.execute("SELECT id FROM owner_info LIMIT 1").fetchone()

    fields = (
        data.get('company_name', ''), data.get('address', ''), data.get('city', ''),
        data.get('state_name', ''), data.get('state_code', ''), data.get('gstin', ''),
        data.get('phone', ''), data.get('email', ''), data.get('bank_name', ''),
        data.get('account_no', ''), data.get('ifsc_code', ''), data.get('branch', ''),
        data.get('declaration_text', '')
    )

    if existing:
        db.execute("""
            UPDATE owner_info SET
                company_name=?, address=?, city=?, state_name=?, state_code=?, 
                gstin=?, phone=?, email=?, bank_name=?, account_no=?, 
                ifsc_code=?, branch=?, declaration_text=?
            WHERE id=?
        """, fields + (existing['id'],))
    else:
        db.execute("""
            INSERT INTO owner_info (company_name, address, city, state_name,
                state_code, gstin, phone, email, bank_name, account_no,
                ifsc_code, branch, declaration_text)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, fields)
    db.commit()
    db.close()
    return jsonify({"status": "success"})

# ============================================================
# ROUTES — CUSTOMERS
# ============================================================
@app.route('/api/customers', methods=['GET'])
def get_customers():
    db = get_db()
    customers = db.execute("SELECT * FROM customers ORDER BY customer_name").fetchall()
    db.close()
    return jsonify([dict(c) for c in customers])

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    db = get_db()
    cur = db.execute("""
        INSERT INTO customers (customer_name, address, city, state_name, state_code, gstin, phone, email)
        VALUES (?,?,?,?,?,?,?,?)
    """, (data.get('customer_name', ''), data.get('address', ''), data.get('city', ''), data.get('state_name', ''), data.get('state_code', ''), data.get('gstin', ''), data.get('phone', ''), data.get('email', '')))
    db.commit()
    new_id = cur.lastrowid
    db.close()
    return jsonify({"status": "success", "id": new_id})

# ============================================================
# ROUTES — PRODUCTS
# ============================================================
@app.route('/api/products', methods=['GET'])
def get_products():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY product_name").fetchall()
    db.close()
    return jsonify([dict(p) for p in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    db = get_db()
    cur = db.execute("""
        INSERT INTO products (product_name, hsn, default_price, default_tax, unit)
        VALUES (?,?,?,?,?)
    """, (data.get('product_name', ''), data.get('hsn', ''), data.get('default_price', 0), data.get('default_tax', 0), data.get('unit', 'Nos')))
    db.commit()
    new_id = cur.lastrowid
    db.close()
    return jsonify({"status": "success", "id": new_id})

# ============================================================
# ROUTES — INVOICES
# ============================================================
@app.route('/api/invoices/next-number', methods=['GET'])
def next_invoice_number():
    db = get_db()
    counter = db.execute("SELECT * FROM invoice_counter LIMIT 1").fetchone()
    if counter:
        next_num = counter['last_number'] + 1
        prefix = counter['prefix']
    else:
        next_num = 1
        prefix = "INV"
    invoice_no = f"{prefix}-{str(next_num).zfill(4)}"
    db.close()
    return jsonify({"invoice_no": invoice_no, "next_num": next_num})

@app.route('/api/invoices', methods=['POST'])
def save_invoice():
    data = request.json or {}
    db = get_db()
    
    try:
        invoice_no = data.get('invoice_no')
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cur = db.execute("""
            INSERT INTO invoices (
                invoice_no, invoice_date, buyer_name, buyer_address, buyer_city, buyer_state,
                buyer_state_code, buyer_gstin, buyer_phone, ship_to_name, ship_to_address,
                ship_to_city, ship_to_state, ship_to_state_code, ship_to_gstin,
                delivery_note, payment_mode, reference_no, other_references,
                buyer_order_no, buyer_order_date, dispatch_doc_no, delivery_note_date,
                dispatched_through, destination, terms_of_delivery, tax_type,
                custom_tax_rate, subtotal, tax_amount, grand_total
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            invoice_no, date_str, data.get('buyer_name'), data.get('buyer_address'),
            data.get('buyer_city'), data.get('buyer_state'), data.get('buyer_state_code'),
            data.get('buyer_gstin'), data.get('buyer_phone'), data.get('ship_to_name'),
            data.get('ship_to_address'), data.get('ship_to_city'), data.get('ship_to_state'),
            data.get('ship_to_state_code'), data.get('ship_to_gstin'), data.get('delivery_note'),
            data.get('payment_mode'), data.get('reference_no'), data.get('other_references'),
            data.get('buyer_order_no'), data.get('buyer_order_date'), data.get('dispatch_doc_no'),
            data.get('delivery_note_date'), data.get('dispatched_through'), data.get('destination'),
            data.get('terms_of_delivery'), data.get('tax_type', 'igst'),
            data.get('custom_tax_rate', 0), data.get('subtotal', 0),
            data.get('tax_amount', 0), data.get('grand_total', 0)
        ))
        
        saved_invoice_id = cur.lastrowid

        # Save Items
        items = data.get('items', [])
        for item in items:
            db.execute("""
                INSERT INTO invoice_items (
                    invoice_id, sl_no, description, hsn, quantity, rate, per_unit, discount_percent, amount
                ) VALUES (?,?,?,?,?,?,?,?,?)
            """, (saved_invoice_id, item.get('sl_no'), item.get('description'), item.get('hsn'),
                  item.get('quantity', 0), item.get('rate', 0), item.get('per_unit', 'Nos'),
                  item.get('discount_percent', 0), item.get('amount', 0)))

        db.commit()
        return jsonify({"status": "success", "invoice_id": saved_invoice_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

# ============================================================
# ROUTES — PDF GENERATION (Fixed Words Passing)
# ============================================================
@app.route('/api/invoices/<int:inv_id>/pdf', methods=['GET'])
def generate_pdf(inv_id):
    if not WEASY_AVAILABLE:
        return jsonify({"error": "PDF Engine not ready"}), 500

    db = get_db()
    invoice = db.execute("SELECT * FROM invoices WHERE id=?", (inv_id,)).fetchone()
    if not invoice:
        db.close()
        return jsonify({"error": "Invoice not found"}), 404

    items = db.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY sl_no", (inv_id,)).fetchall()
    owner = db.execute("SELECT * FROM owner_info LIMIT 1").fetchone()
    db.close()

    # THE FIX: Calculate words for BOTH Grand Total and Tax specifically
    grand_total_words = number_to_words(invoice['grand_total'])
    tax_amount_words = number_to_words(invoice['tax_amount'])

    html_content = render_template(
        'invoice_print.html',
        invoice=dict(invoice),
        items=[dict(i) for i in items],
        owner=dict(owner) if owner else {},
        grand_total_words=grand_total_words,
        tax_amount_words=tax_amount_words,
        states=INDIAN_STATES
    )

    pdf = WeasyHTML(string=html_content, base_url=request.url_root).write_pdf()

    return Response(
        pdf, mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={invoice["invoice_no"]}.pdf'}
    )

@app.route('/api/number-to-words', methods=['GET'])
def api_number_to_words():
    amount = float(request.args.get('amount', 0))
    return jsonify({"words": number_to_words(amount)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

    