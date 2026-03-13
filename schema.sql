-- schema.sql
-- Database schema for Tax Invoice Application

CREATE DATABASE IF NOT EXISTS tax_invoice_db;
USE tax_invoice_db;

-- ============================================================
-- Table: owner_info
-- ============================================================
CREATE TABLE IF NOT EXISTS owner_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    state_name VARCHAR(100),
    state_code VARCHAR(10),
    gstin VARCHAR(15),
    phone VARCHAR(20),
    email VARCHAR(255),
    bank_name VARCHAR(255),
    account_no VARCHAR(50),
    ifsc_code VARCHAR(20),
    branch VARCHAR(255),
    declaration_text TEXT
);

-- Insert default owner info (only if table empty)
INSERT INTO owner_info 
(company_name, address, city, state_name, state_code, gstin, phone, email, declaration_text)
SELECT 
'National Enterprises',
'HSR Layout',
'Bangalore',
'Karnataka',
'29',
'29AACCT3705E000',
'+919876543210',
'info@nationalenterprises.com',
'We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.'
WHERE NOT EXISTS (SELECT 1 FROM owner_info);

-- ============================================================
-- Table: customers
-- ============================================================
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    state_name VARCHAR(100),
    state_code VARCHAR(10),
    gstin VARCHAR(15),
    phone VARCHAR(20),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Table: products
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    hsn VARCHAR(20),
    default_price DECIMAL(12,2) DEFAULT 0.00,
    default_tax DECIMAL(5,2) DEFAULT 0.00,
    unit VARCHAR(20) DEFAULT 'Nos',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample products
INSERT INTO products (product_name, hsn, default_price, default_tax, unit) VALUES
('12MM TMT Bar','1004',50.00,12.00,'Nos'),
('8MM TMT Bar','1004',40.00,12.00,'Nos'),
('Cement 50kg Bag','2523',350.00,28.00,'Nos'),
('Sand (per ton)','2505',1200.00,5.00,'Kg'),
('Bricks (per 1000)','6901',6000.00,5.00,'Nos');

-- ============================================================
-- Table: invoices
-- ============================================================
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_no VARCHAR(50) NOT NULL UNIQUE,
    invoice_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    buyer_name VARCHAR(255),
    buyer_address VARCHAR(500),
    buyer_city VARCHAR(100),
    buyer_state VARCHAR(100),
    buyer_state_code VARCHAR(10),
    buyer_gstin VARCHAR(15),
    buyer_phone VARCHAR(20),

    ship_to_name VARCHAR(255),
    ship_to_address VARCHAR(500),
    ship_to_city VARCHAR(100),
    ship_to_state VARCHAR(100),
    ship_to_state_code VARCHAR(10),
    ship_to_gstin VARCHAR(15),

    delivery_note VARCHAR(255),
    payment_mode VARCHAR(50),
    reference_no VARCHAR(255),
    other_references VARCHAR(255),
    buyer_order_no VARCHAR(255),
    buyer_order_date VARCHAR(100),
    dispatch_doc_no VARCHAR(255),
    delivery_note_date VARCHAR(100),
    dispatched_through VARCHAR(255),
    destination VARCHAR(255),
    terms_of_delivery TEXT,

    tax_type VARCHAR(20) DEFAULT 'igst',
    custom_tax_rate DECIMAL(5,2) DEFAULT 0.00,

    subtotal DECIMAL(12,2) DEFAULT 0.00,
    tax_amount DECIMAL(12,2) DEFAULT 0.00,
    grand_total DECIMAL(12,2) DEFAULT 0.00,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Table: invoice_items
-- ============================================================
CREATE TABLE IF NOT EXISTS invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    sl_no INT,
    description VARCHAR(500),
    hsn VARCHAR(20),
    quantity DECIMAL(12,3) DEFAULT 0,
    rate DECIMAL(12,2) DEFAULT 0.00,
    per_unit VARCHAR(20) DEFAULT 'Nos',
    discount_percent DECIMAL(5,2) DEFAULT 0.00,
    amount DECIMAL(12,2) DEFAULT 0.00,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

-- ============================================================
-- Table: invoice_counter
-- ============================================================
CREATE TABLE IF NOT EXISTS invoice_counter (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prefix VARCHAR(10) DEFAULT 'INV',
    last_number INT DEFAULT 0
);

INSERT INTO invoice_counter (prefix,last_number)
SELECT 'INV',0
WHERE NOT EXISTS (SELECT 1 FROM invoice_counter);