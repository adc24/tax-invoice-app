/**
 * invoice.js
 * ==========
 * Client-side JavaScript for the Tax Invoice Web Application.
 * Handles: navigation, product rows, calculations, autocomplete,
 * customer selection, save/load, print, PDF download.
 */
let products = [];
let customers = [];
let currentInvoiceId = null;
let editingCustomerId = null;
let editingProductId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadOwnerInfo();
    loadCustomers();
    loadProducts();
    addProductRow();
    setDefaultDate();
});

function switchToPanel(id) {
    document.querySelectorAll('.panel, .invoice-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

function setDefaultDate() {
    document.getElementById('invoice-date').value = new Date().toISOString().slice(0, 16);
}

// --- OWNER INFO ---
function loadOwnerInfo() {
    fetch('/api/owner').then(r => r.json()).then(data => {
        document.getElementById('owner-company').value = data.company_name || '';
        document.getElementById('owner-gstin').value = data.gstin || '';
        document.getElementById('owner-address').value = data.address || '';
        // Also populate edit form
        if(document.getElementById('edit-owner-company')) {
            document.getElementById('edit-owner-company').value = data.company_name || '';
            document.getElementById('edit-owner-gstin').value = data.gstin || '';
        }
    });
}

function saveOwnerInfo() {
    const data = {
        company_name: document.getElementById('edit-owner-company').value,
        gstin: document.getElementById('edit-owner-gstin').value,
        address: document.getElementById('edit-owner-address').value
    };
    fetch('/api/owner', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    }).then(() => { showToast('Owner Saved'); loadOwnerInfo(); });
}

// --- CUSTOMERS ---
function loadCustomers() {
    fetch('/api/customers').then(r => r.json()).then(data => {
        customers = data;
        renderCustomers();
        const sel = document.getElementById('customer-select');
        sel.innerHTML = '<option value="">-- Select --</option>';
        data.forEach(c => sel.innerHTML += `<option value="${c.id}">${c.customer_name}</option>`);
    });
}

function renderCustomers() {
    const list = document.getElementById('customer-list');
    list.innerHTML = '<table class="data-table"><thead><tr><th>Name</th><th>GSTIN</th><th>Actions</th></tr></thead><tbody id="cust-body"></tbody></table>';
    customers.forEach(c => {
        document.getElementById('cust-body').innerHTML += `<tr><td>${c.customer_name}</td><td>${c.gstin}</td>
            <td><button onclick="startEditCustomer(${c.id})">Edit</button> <button onclick="deleteCustomer(${c.id})">Delete</button></td></tr>`;
    });
}

function startEditCustomer(id) {
    const c = customers.find(x => x.id === id);
    editingCustomerId = id;
    document.getElementById('new-cust-name').value = c.customer_name;
    document.getElementById('new-cust-gstin').value = c.gstin;
    document.getElementById('add-customer-btn').textContent = 'Update';
}

function deleteCustomer(id) {
    if(confirm('Delete?')) fetch(`/api/customers/${id}`, {method: 'DELETE'}).then(loadCustomers);
}

function addCustomer() {
    const data = { customer_name: document.getElementById('new-cust-name').value, gstin: document.getElementById('new-cust-gstin').value };
    const method = editingCustomerId ? 'PUT' : 'POST';
    const url = editingCustomerId ? `/api/customers/${editingCustomerId}` : '/api/customers';
    fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) }).then(() => {
        editingCustomerId = null;
        document.getElementById('add-customer-btn').textContent = 'Add';
        loadCustomers();
    });
}

// --- PRODUCTS ---
function loadProducts() {
    fetch('/api/products').then(r => r.json()).then(data => { products = data; renderProducts(); });
}

function renderProducts() {
    const body = document.getElementById('product-catalog-list');
    body.innerHTML = '<table class="data-table"><thead><tr><th>Product</th><th>Price</th><th>Actions</th></tr></thead><tbody id="prod-body"></tbody></table>';
    products.forEach(p => {
        document.getElementById('prod-body').innerHTML += `<tr><td>${p.product_name}</td><td>${p.default_price}</td>
            <td><button onclick="deleteProduct(${p.id})">Delete</button></td></tr>`;
    });
}

function deleteProduct(id) {
    if(confirm('Delete?')) fetch(`/api/products/${id}`, {method: 'DELETE'}).then(loadProducts);
}

function addProductToCatalog() {
    const data = { product_name: document.getElementById('new-product-name').value, default_price: document.getElementById('new-product-price').value };
    fetch('/api/products', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) }).then(loadProducts);
}

// --- INVOICE LOGIC ---
let rowCount = 0;
function addProductRow() {
    rowCount++;
    const tbody = document.getElementById('product-tbody');
    const tr = document.createElement('tr');
    tr.id = `row-${rowCount}`;
    tr.innerHTML = `<td>${rowCount}</td><td><input type="text" class="desc-input" oninput="recalculate()"></td>
        <td><input type="text"></td><td><input type="number" class="qty-input" value="1" oninput="recalculate()"></td>
        <td><input type="number" class="rate-input" value="0" oninput="recalculate()"></td><td>Nos</td>
        <td><input type="number" class="disc-input" value="0" oninput="recalculate()"></td><td class="amount-cell">0.00</td>`;
    tbody.appendChild(tr);
}

function recalculate() {
    let subtotal = 0;
    document.querySelectorAll('#product-tbody tr').forEach(row => {
        const qty = parseFloat(row.querySelector('.qty-input').value) || 0;
        const rate = parseFloat(row.querySelector('.rate-input').value) || 0;
        const disc = parseFloat(row.querySelector('.disc-input').value) || 0;
        const amt = (qty * rate) * (1 - disc/100);
        row.querySelector('.amount-cell').textContent = amt.toFixed(2);
        subtotal += amt;
    });
    document.getElementById('subtotal-amount').textContent = subtotal.toFixed(2);
    document.getElementById('grand-total-display').textContent = `₹ ${subtotal.toFixed(2)}`;
    updateWords(subtotal);
}

function updateWords(amt) {
    fetch(`/api/number-to-words?amount=${amt}`).then(r => r.json()).then(data => {
        document.getElementById('amount-words').textContent = data.words;
    });
}

function saveInvoice() {
    const data = { 
        invoice_no: document.getElementById('invoice-no').value,
        grand_total: document.getElementById('subtotal-amount').textContent,
        buyer_name: document.getElementById('bill-name').value
    };
    fetch('/api/invoices', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) })
        .then(r => r.json()).then(res => { currentInvoiceId = res.invoice_id; showToast('Saved'); });
}

function downloadPDF() {
    if(!currentInvoiceId) { alert('Save first'); return; }
    window.location.href = `/api/invoices/${currentInvoiceId}/pdf`;
}

function newInvoice() {
    document.getElementById('product-tbody').innerHTML = '';
    document.getElementById('bill-name').value = '';
    addProductRow();
    loadOwnerInfo();
    recalculate();
}

function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg; t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3000);
}