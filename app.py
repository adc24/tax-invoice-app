"""
app.py
------
Flask backend for the Tax Invoice Web Application.
Handles all routes: serving pages, CRUD for customers/products/invoices,
PDF generation, and invoice number auto-increment.
"""

from flask import Flask, render_template, request, jsonify, Response
from datetime import datetime
import mysql.connector
import json
from config import DB_CONFIG, SECRET_KEY, INVOICE_PREFIX

# Try importing WeasyPrint for PDF generation
try:
    from weasyprint import HTML as WeasyHTML
    WEASY_AVAILABLE = True
except ImportError:
    WEASY_AVAILABLE = False
    print("WARNING: WeasyPrint not installed. PDF download will not work.")

# Try importing num2words for number-to-words conversion
try:
    from num2words import num2words
    NUM2WORDS_AVAILABLE = True
except ImportError:
    NUM2WORDS_AVAILABLE = False
    print("WARNING: num2words not installed. Using basic conversion.")

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ============================================================
# DATABASE HELPER
# ============================================================
def get_db():
    """Create and return a MySQL database connection."""
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
# NUMBER TO WORDS CONVERSION
# ============================================================
def number_to_words(amount):
    """Convert a numeric amount to Indian English words.
    Example: 560.00 -> 'Indian Rupee Five Hundred Sixty Only'
    """
    if NUM2WORDS_AVAILABLE:
        # Split into rupees and paise
        rupees = int(amount)
        paise = round((amount - rupees) * 100)
        words = num2words(rupees, lang='en_IN').title()
        if paise > 0:
            paise_words = num2words(paise, lang='en_IN').title()
            return f"Indian Rupee {words} and {paise_words} Paise Only"
        return f"Indian Rupee {words} Only"
    else:
        return f"Indian Rupee {int(amount)} Only"


# ============================================================
# INDIAN STATES LIST (for dropdown)
# ============================================================
INDIAN_STATES = [
    {"name": "Andhra Pradesh", "code": "37"},
    {"name": "Arunachal Pradesh", "code": "12"},
    {"name": "Assam", "code": "18"},
    {"name": "Bihar", "code": "10"},
    {"name": "Chhattisgarh", "code": "22"},
    {"name": "Delhi", "code": "07"},
    {"name": "Goa", "code": "30"},
    {"name": "Gujarat", "code": "24"},
    {"name": "Haryana", "code": "06"},
    {"name": "Himachal Pradesh", "code": "02"},
    {"name": "Jharkhand", "code": "20"},
    {"name": "Karnataka", "code": "29"},
    {"name": "Kerala", "code": "32"},
    {"name": "Madhya Pradesh", "code": "23"},
    {"name": "Maharashtra", "code": "27"},
    {"name": "Manipur", "code": "14"},
    {"name": "Meghalaya", "code": "17"},
    {"name": "Mizoram", "code": "15"},
    {"name": "Nagaland", "code": "13"},
    {"name": "Odisha", "code": "21"},
    {"name": "Punjab", "code": "03"},
    {"name": "Rajasthan", "code": "08"},
    {"name": "Sikkim", "code": "11"},
    {"name": "Tamil Nadu", "code": "33"},
    {"name": "Telangana", "code": "36"},
    {"name": "Tripura", "code": "16"},
    {"name": "Uttar Pradesh", "code": "09"},
    {"name": "Uttarakhand", "code": "05"},
    {"name": "West Bengal", "code": "19"},
    {"name": "Jammu & Kashmir", "code": "01"},
    {"name": "Ladakh", "code": "38"},
    {"name": "Chandigarh", "code": "04"},
    {"name": "Puducherry", "code": "34"},
    {"name": "Lakshadweep", "code": "31"},
    {"name": "Andaman & Nicobar Islands", "code": "35"},
    {"name": "Dadra & Nagar Haveli and Daman & Diu", "code": "26"},
]


# ============================================================
# ROUTES — PAGES
# ============================================================

@app.route('/')
def index():
    """Serve the main invoice application page."""
    return render_template('invoice.html', states=INDIAN_STATES)


# ============================================================
# ROUTES — OWNER INFO
# ============================================================

@app.route('/api/owner', methods=['GET'])
def get_owner():
    """Retrieve the owner/seller information."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM owner_info LIMIT 1")
    owner = cursor.fetchone()
    cursor.close()
    db.close()
    return jsonify(owner or {})


@app.route('/api/owner', methods=['POST'])
def update_owner():
    """Update the owner/seller information."""
    data = request.json
    db = get_db()
    cursor = db.cursor()
    # Check if owner exists
    cursor.execute("SELECT id FROM owner_info LIMIT 1")
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE owner_info SET
                company_name=%s, address=%s, city=%s, state_name=%s,
                state_code=%s, gstin=%s, phone=%s, email=%s,
                bank_name=%s, account_no=%s, ifsc_code=%s, branch=%s,
                declaration_text=%s
            WHERE id=%s
        """, (
            data.get('company_name', ''), data.get('address', ''),
            data.get('city', ''), data.get('state_name', ''),
            data.get('state_code', ''), data.get('gstin', ''),
            data.get('phone', ''), data.get('email', ''),
            data.get('bank_name', ''), data.get('account_no', ''),
            data.get('ifsc_code', ''), data.get('branch', ''),
            data.get('declaration_text', ''), existing[0]
        ))
    else:
        cursor.execute("""
            INSERT INTO owner_info (company_name, address, city, state_name,
                state_code, gstin, phone, email, bank_name, account_no,
                ifsc_code, branch, declaration_text)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data.get('company_name', ''), data.get('address', ''),
            data.get('city', ''), data.get('state_name', ''),
            data.get('state_code', ''), data.get('gstin', ''),
            data.get('phone', ''), data.get('email', ''),
            data.get('bank_name', ''), data.get('account_no', ''),
            data.get('ifsc_code', ''), data.get('branch', ''),
            data.get('declaration_text', '')
        ))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "success"})


# ============================================================
# ROUTES — CUSTOMERS
# ============================================================

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Retrieve all customers for the dropdown/list."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers ORDER BY customer_name")
    customers = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(customers)

@app.route('/api/customers/<int:cid>', methods=['GET'])
def get_single_customer(cid):
    """Retrieve a single customer by ID."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE id=%s", (cid,))
    customer = cursor.fetchone()
    cursor.close()
    db.close()
    return jsonify(customer or {})

@app.route('/api/customers', methods=['POST'])
def add_customer():
    """Add a new customer to the database."""
    data = request.json
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO customers (customer_name, address, city, state_name,
            state_code, gstin, phone, email)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data.get('customer_name', ''), data.get('address', ''),
        data.get('city', ''), data.get('state_name', ''),
        data.get('state_code', ''), data.get('gstin', ''),
        data.get('phone', ''), data.get('email', '')
    ))
    db.commit()
    new_id = cursor.lastrowid
    cursor.close()
    db.close()
    return jsonify({"status": "success", "id": new_id})

@app.route('/api/customers/<int:cid>', methods=['PUT'])
def update_customer(cid):
    """Update an existing customer."""
    data = request.json
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE customers SET
            customer_name=%s, address=%s, city=%s, state_name=%s,
            state_code=%s, gstin=%s, phone=%s, email=%s
        WHERE id=%s
    """, (
        data.get('customer_name', ''), data.get('address', ''),
        data.get('city', ''), data.get('state_name', ''),
        data.get('state_code', ''), data.get('gstin', ''),
        data.get('phone', ''), data.get('email', ''), cid
    ))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "success"})

@app.route('/api/customers/<int:cid>', methods=['DELETE'])
def delete_customer(cid):
    """Delete a customer by ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM customers WHERE id=%s", (cid,))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "success"})


# ============================================================
# ROUTES — PRODUCTS
# ============================================================

@app.route('/api/products', methods=['GET'])
def get_products():
    """Retrieve all products for autocomplete/catalog."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products ORDER BY product_name")
    products = cursor.fetchall()
    cursor.close()
    db.close()
    # Convert Decimal to float for JSON serialization
    for p in products:
        p['default_price'] = float(p['default_price']) if p['default_price'] else 0
        p['default_tax'] = float(p['default_tax']) if p['default_tax'] else 0
    return jsonify(products)

@app.route('/api/products/<int:pid>', methods=['GET'])
def get_single_product(pid):
    """Retrieve a single product by ID."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id=%s", (pid,))
    product = cursor.fetchone()
    if product:
        product['default_price'] = float(product['default_price']) if product['default_price'] else 0
        product['default_tax'] = float(product['default_tax']) if product['default_tax'] else 0
    cursor.close()
    db.close()
    return jsonify(product or {})

@app.route('/api/products', methods=['POST'])
def add_product():
    """Add a new product to the catalog."""
    data = request.json
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO products (product_name, hsn, default_price, default_tax, unit)
        VALUES (%s,%s,%s,%s,%s)
    """, (
        data.get('product_name', ''), data.get('hsn', ''),
        data.get('default_price', 0), data.get('default_tax', 0),
        data.get('unit', 'Nos')
    ))
    db.commit()
    new_id = cursor.lastrowid
    cursor.close()
    db.close()
    return jsonify({"status": "success", "id": new_id})

@app.route('/api/products/<int:pid>', methods=['PUT'])
def update_product(pid):
    """Update an existing product."""
    data = request.json
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE products SET
            product_name=%s, hsn=%s, default_price=%s, default_tax=%s, unit=%s
        WHERE id=%s
    """, (
        data.get('product_name', ''), data.get('hsn', ''),
        data.get('default_price', 0), data.get('default_tax', 0),
        data.get('unit', 'Nos'), pid
    ))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "success"})

@app.route('/api/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    """Delete a product by ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s", (pid,))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "success"})

@app.route('/api/products/search', methods=['GET'])
def search_products():
    """Search products by name for autocomplete."""
    query = request.args.get('q', '')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM products WHERE product_name LIKE %s LIMIT 10",
        (f'%{query}%',)
    )
    products = cursor.fetchall()
    cursor.close()
    db.close()
    for p in products:
        p['default_price'] = float(p['default_price']) if p['default_price'] else 0
        p['default_tax'] = float(p['default_tax']) if p['default_tax'] else 0
    return jsonify(products)


# ============================================================
# ROUTES — INVOICES
# ============================================================

@app.route('/api/invoices/next-number', methods=['GET'])
def next_invoice_number():
    """Generate the next auto-incremented invoice number."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM invoice_counter LIMIT 1")
    counter = cursor.fetchone()
    if counter:
        next_num = counter['last_number'] + 1
        prefix = counter['prefix']
    else:
        next_num = 1
        prefix = INVOICE_PREFIX
    invoice_no = f"{prefix}-{str(next_num).zfill(4)}"
    cursor.close()
    db.close()
    return jsonify({"invoice_no": invoice_no, "next_num": next_num})


@app.route('/api/invoices', methods=['POST'])
def save_invoice():
    """Save or update an invoice (header + line items)."""
    data = request.json or {}
    db = get_db()
    cursor = db.cursor()

    def normalize_invoice_datetime(raw_value):
        """Convert datetime-local values to MySQL DATETIME format."""
        if not raw_value:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
            try:
                return datetime.strptime(raw_value, fmt).strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue

        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        invoice_id = data.get('invoice_id')
        invoice_date = normalize_invoice_datetime(data.get('invoice_date'))

        # Common field tuple used by both INSERT and UPDATE
        invoice_values = (
            data.get('invoice_no'), invoice_date,
            data.get('buyer_name'), data.get('buyer_address'),
            data.get('buyer_city'), data.get('buyer_state'),
            data.get('buyer_state_code'), data.get('buyer_gstin'),
            data.get('buyer_phone'),
            data.get('ship_to_name'), data.get('ship_to_address'),
            data.get('ship_to_city'), data.get('ship_to_state'),
            data.get('ship_to_state_code'), data.get('ship_to_gstin'),
            data.get('delivery_note'), data.get('payment_mode'),
            data.get('reference_no'), data.get('other_references'),
            data.get('buyer_order_no'), data.get('buyer_order_date'),
            data.get('dispatch_doc_no'), data.get('delivery_note_date'),
            data.get('dispatched_through'), data.get('destination'),
            data.get('terms_of_delivery'),
            data.get('tax_type', 'igst'), data.get('custom_tax_rate', 0),
            data.get('subtotal', 0), data.get('tax_amount', 0),
            data.get('grand_total', 0)
        )

        if invoice_id:
            # EDIT MODE: update header and replace line items
            cursor.execute("SELECT id FROM invoices WHERE id=%s", (invoice_id,))
            existing = cursor.fetchone()
            if not existing:
                return jsonify({"error": "Invoice not found"}), 404

            cursor.execute("""
                UPDATE invoices SET
                    invoice_no=%s, invoice_date=%s,
                    buyer_name=%s, buyer_address=%s, buyer_city=%s, buyer_state=%s,
                    buyer_state_code=%s, buyer_gstin=%s, buyer_phone=%s,
                    ship_to_name=%s, ship_to_address=%s, ship_to_city=%s,
                    ship_to_state=%s, ship_to_state_code=%s, ship_to_gstin=%s,
                    delivery_note=%s, payment_mode=%s, reference_no=%s,
                    other_references=%s, buyer_order_no=%s, buyer_order_date=%s,
                    dispatch_doc_no=%s, delivery_note_date=%s,
                    dispatched_through=%s, destination=%s, terms_of_delivery=%s,
                    tax_type=%s, custom_tax_rate=%s,
                    subtotal=%s, tax_amount=%s, grand_total=%s
                WHERE id=%s
            """, invoice_values + (invoice_id,))

            cursor.execute("DELETE FROM invoice_items WHERE invoice_id=%s", (invoice_id,))
            saved_invoice_id = invoice_id
            mode = 'updated'
        else:
            # CREATE MODE: increment counter and insert a new invoice
            cursor.execute("SELECT id, prefix, last_number FROM invoice_counter ORDER BY id ASC LIMIT 1")
            counter = cursor.fetchone()
            if counter:
                counter_id, prefix, last_number = counter
            else:
                cursor.execute(
                    "INSERT INTO invoice_counter (prefix, last_number) VALUES (%s, %s)",
                    (INVOICE_PREFIX, 0)
                )
                counter_id, prefix, last_number = cursor.lastrowid, INVOICE_PREFIX, 0

            next_number = int(last_number) + 1
            cursor.execute("UPDATE invoice_counter SET last_number=%s WHERE id=%s", (next_number, counter_id))

            invoice_no = data.get('invoice_no')
            if not invoice_no:
                invoice_no = f"{prefix}-{str(next_number).zfill(4)}"

            insert_values = (invoice_no,) + invoice_values[1:]

            cursor.execute("""
                INSERT INTO invoices (
                    invoice_no, invoice_date,
                    buyer_name, buyer_address, buyer_city, buyer_state,
                    buyer_state_code, buyer_gstin, buyer_phone,
                    ship_to_name, ship_to_address, ship_to_city,
                    ship_to_state, ship_to_state_code, ship_to_gstin,
                    delivery_note, payment_mode, reference_no,
                    other_references, buyer_order_no, buyer_order_date,
                    dispatch_doc_no, delivery_note_date,
                    dispatched_through, destination, terms_of_delivery,
                    tax_type, custom_tax_rate,
                    subtotal, tax_amount, grand_total
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
            """, insert_values)

            saved_invoice_id = cursor.lastrowid
            mode = 'created'

        # Insert each line item (for both create and update)
        items = data.get('items', [])
        for item in items:
            cursor.execute("""
                INSERT INTO invoice_items (
                    invoice_id, sl_no, description, hsn,
                    quantity, rate, per_unit, discount_percent, amount
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                saved_invoice_id, item.get('sl_no'), item.get('description'),
                item.get('hsn'), item.get('quantity', 0),
                item.get('rate', 0), item.get('per_unit', 'Nos'),
                item.get('discount_percent', 0), item.get('amount', 0)
            ))

        db.commit()
        return jsonify({"status": "success", "invoice_id": saved_invoice_id, "mode": mode})

    except mysql.connector.IntegrityError as err:
        db.rollback()
        return jsonify({"error": f"Unable to save invoice: {err.msg}"}), 400
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        cursor.close()
        db.close()


@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    """Retrieve all saved invoices (summary list)."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, invoice_no, invoice_date, buyer_name, grand_total
        FROM invoices ORDER BY created_at DESC
    """)
    invoices = cursor.fetchall()
    cursor.close()
    db.close()
    # Convert types for JSON
    for inv in invoices:
        inv['grand_total'] = float(inv['grand_total']) if inv['grand_total'] else 0
        if inv['invoice_date']:
            inv['invoice_date'] = inv['invoice_date'].strftime('%Y-%m-%d %H:%M')
    return jsonify(invoices)


@app.route('/api/invoices/<int:inv_id>', methods=['GET'])
def get_invoice(inv_id):
    """Retrieve a single invoice with all its line items."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM invoices WHERE id=%s", (inv_id,))
    invoice = cursor.fetchone()
    if not invoice:
        cursor.close()
        db.close()
        return jsonify({"error": "Invoice not found"}), 404

    # Convert Decimal fields
    for key in ['subtotal', 'tax_amount', 'grand_total', 'custom_tax_rate']:
        if invoice.get(key):
            invoice[key] = float(invoice[key])
    if invoice.get('invoice_date'):
        invoice['invoice_date'] = invoice['invoice_date'].strftime('%Y-%m-%dT%H:%M')

    # Get line items
    cursor.execute("SELECT * FROM invoice_items WHERE invoice_id=%s ORDER BY sl_no", (inv_id,))
    items = cursor.fetchall()
    for item in items:
        for key in ['quantity', 'rate', 'discount_percent', 'amount']:
            if item.get(key):
                item[key] = float(item[key])
    invoice['items'] = items

    cursor.close()
    db.close()
    return jsonify(invoice)


@app.route('/api/invoices/<int:inv_id>', methods=['DELETE'])
def delete_invoice(inv_id):
    """Delete an invoice and its items."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM invoices WHERE id=%s", (inv_id,))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "success"})


# ============================================================
# ROUTES — PDF GENERATION
# ============================================================

@app.route('/api/invoices/<int:inv_id>/pdf', methods=['GET'])
def generate_pdf(inv_id):
    """Generate a PDF for a specific invoice using WeasyPrint."""
    if not WEASY_AVAILABLE:
        return jsonify({"error": "WeasyPrint not installed"}), 500

    # Fetch invoice data
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM invoices WHERE id=%s", (inv_id,))
    invoice = cursor.fetchone()
    if not invoice:
        cursor.close()
        db.close()
        return jsonify({"error": "Invoice not found"}), 404

    for key in ['subtotal', 'tax_amount', 'grand_total', 'custom_tax_rate']:
        if invoice.get(key):
            invoice[key] = float(invoice[key])

    cursor.execute("SELECT * FROM invoice_items WHERE invoice_id=%s ORDER BY sl_no", (inv_id,))
    items = cursor.fetchall()
    for item in items:
        for key in ['quantity', 'rate', 'discount_percent', 'amount']:
            if item.get(key):
                item[key] = float(item[key])

    # Fetch owner info
    cursor.execute("SELECT * FROM owner_info LIMIT 1")
    owner = cursor.fetchone()
    cursor.close()
    db.close()

    # Convert totals to words
    grand_total_words = number_to_words(float(invoice.get('grand_total', 0)))
    tax_amount_words = number_to_words(float(invoice.get('tax_amount', 0)))

    # Render the print-mode HTML
    html_content = render_template(
        'invoice_print.html',
        invoice=invoice,
        items=items,
        owner=owner or {},
        grand_total_words=grand_total_words,
        tax_amount_words=tax_amount_words,
        states=INDIAN_STATES
    )

    # Generate PDF from HTML
    # FIXED: Added base_url=request.url_root and variant to fix PDF engine errors
    pdf = WeasyHTML(string=html_content, base_url=request.url_root).write_pdf(variant='pdf/a-1b')

    return Response(
        pdf,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename={invoice["invoice_no"]}.pdf'
        }
    )


@app.route('/api/number-to-words', methods=['GET'])
def api_number_to_words():
    """API endpoint to convert a number to words."""
    amount = float(request.args.get('amount', 0))
    return jsonify({"words": number_to_words(amount)})


# ============================================================
# RUN THE APPLICATION
# ============================================================
if __name__ == '__main__':
    print("Starting Tax Invoice Application...")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True, port=5000)