/**
 * invoice.js
 * ==========
 * Client-side JavaScript for the Tax Invoice Web Application.
 * Handles: navigation, product rows, calculations, autocomplete,
 * customer selection, save/load, print, PDF download.
 */

// ============================================================
// GLOBAL STATE
// ============================================================
let products = [];      // Cached product catalog
let customers = [];     // Cached customer list
let ownerInfo = {};     // Cached owner info
let currentInvoiceId = null; // Currently opened invoice ID (for edit/update)
let currentProductId = null; // Currently editing product ID
let currentCustomerId = null; // Currently editing customer ID
let isInvoiceReadOnly = false; // True when opened in view mode

// ============================================================
// INITIALIZATION — Runs when page loads
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data from server
    loadOwnerInfo();
    loadProducts();
    loadCustomers();
    fetchNextInvoiceNumber();
    setDefaultDateTime();
    
    // Setup navigation
    setupNavigation();
    
    // Setup tax type radio buttons
    setupTaxSelector();
    
    // Setup ship-to = bill-to checkbox
    setupShipBillToggle();
    
    // Add one empty product row by default
    addProductRow();
    
    // Recalculate on any change
    recalculate();
});


// ============================================================
// NAVIGATION — Sidebar panel switching
// ============================================================
function setupNavigation() {
    /** Attach click handlers to sidebar nav buttons */
    const navBtns = document.querySelectorAll('.sidebar-nav button');
    navBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            navBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Show the target panel, hide others
            const target = this.dataset.target;
            document.querySelectorAll('.panel, .invoice-panel').forEach(p => {
                p.classList.remove('active');
            });
            const panel = document.getElementById(target);
            if (panel) panel.classList.add('active');
        });
    });
}

/**
 * Switch to a specific panel programmatically
 * @param {string} panelId - The ID of the panel to show
 */
function switchToPanel(panelId) {
    const navBtns = document.querySelectorAll('.sidebar-nav button');
    navBtns.forEach(b => {
        b.classList.remove('active');
        if (b.dataset.target === panelId) b.classList.add('active');
    });
    document.querySelectorAll('.panel, .invoice-panel').forEach(p => {
        p.classList.remove('active');
    });
    const panel = document.getElementById(panelId);
    if (panel) panel.classList.add('active');
}

// ============================================================
// API HELPERS — Consistent response/error handling
// ============================================================
async function parseApiResponse(response) {
    /** Parse JSON responses and surface backend errors clearly */
    const text = await response.text();
    let payload = {};

    if (text) {
        try {
            payload = JSON.parse(text);
        } catch {
            payload = { error: text.slice(0, 200) };
        }
    }

    if (!response.ok) {
        throw new Error(payload.error || payload.message || `Request failed (${response.status})`);
    }

    return payload;
}


function loadOwnerInfo() {
    /** Fetch owner info from server and populate the invoice header */
    fetch('/api/owner')
        .then(r => r.json())
        .then(data => {
            ownerInfo = data;
            // Populate invoice header
            if (data.company_name) {
                document.getElementById('owner-company').value = data.company_name || '';
                document.getElementById('owner-address').value = data.address || '';
                document.getElementById('owner-city').value = data.city || '';
                // Set state dropdown
                const stateSelect = document.getElementById('owner-state');
                if (stateSelect && data.state_name) {
                    stateSelect.value = data.state_name;
                    document.getElementById('owner-state-code').textContent = data.state_code || '';
                }
                document.getElementById('owner-gstin').value = data.gstin || '';
            }
            // Populate owner edit panel
            if (document.getElementById('edit-owner-company')) {
                document.getElementById('edit-owner-company').value = data.company_name || '';
                document.getElementById('edit-owner-address').value = data.address || '';
                document.getElementById('edit-owner-city').value = data.city || '';
                document.getElementById('edit-owner-state').value = data.state_name || '';
                document.getElementById('edit-owner-gstin').value = data.gstin || '';
                document.getElementById('edit-owner-phone').value = data.phone || '';
                document.getElementById('edit-owner-email').value = data.email || '';
                document.getElementById('edit-owner-bank').value = data.bank_name || '';
                document.getElementById('edit-owner-account').value = data.account_no || '';
                document.getElementById('edit-owner-ifsc').value = data.ifsc_code || '';
                document.getElementById('edit-owner-branch').value = data.branch || '';
                document.getElementById('edit-owner-declaration').value = data.declaration_text || '';
            }
        })
        .catch(err => console.error('Error loading owner info:', err));
}

function saveOwnerInfo() {
    /** Save owner info from the edit panel to the server */
    const data = {
        company_name: document.getElementById('edit-owner-company').value,
        address: document.getElementById('edit-owner-address').value,
        city: document.getElementById('edit-owner-city').value,
        state_name: document.getElementById('edit-owner-state').value,
        state_code: getStateCode(document.getElementById('edit-owner-state').value),
        gstin: document.getElementById('edit-owner-gstin').value,
        phone: document.getElementById('edit-owner-phone').value,
        email: document.getElementById('edit-owner-email').value,
        bank_name: document.getElementById('edit-owner-bank').value,
        account_no: document.getElementById('edit-owner-account').value,
        ifsc_code: document.getElementById('edit-owner-ifsc').value,
        branch: document.getElementById('edit-owner-branch').value,
        declaration_text: document.getElementById('edit-owner-declaration').value
    };
    
    fetch('/api/owner', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(() => {
        showToast('Owner info saved successfully');
        loadOwnerInfo();
    })
    .catch(err => showToast('Error saving owner info', true));
}


// ============================================================
// PRODUCTS — Load, add, edit, delete
// ============================================================
function loadProducts() {
    fetch('/api/products')
        .then(parseApiResponse)
        .then(data => {
            products = data;
            renderProductCatalog();
        })
        .catch(err => console.error('Error loading products:', err));
}

function renderProductCatalog() {
    const list = document.getElementById('product-catalog-list');
    if (!list) return;
    
    if (products.length === 0) {
        list.innerHTML = '<p style="color:#6b7280; font-size:13px;">No products yet.</p>';
        return;
    }
    
    let html = `<table class="data-table">
        <thead><tr><th>Product Name</th><th>HSN</th><th>Price</th><th>Tax %</th><th>Unit</th><th>Action</th></tr></thead>
        <tbody>`;
    
    products.forEach(p => {
        html += `<tr>
            <td>${p.product_name}</td>
            <td>${p.hsn || '-'}</td>
            <td>₹${parseFloat(p.default_price).toFixed(2)}</td>
            <td>${p.default_tax}%</td>
            <td>${p.unit}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="editProduct(${p.id})">Edit</button>
                <button class="btn btn-danger btn-sm" onclick="deleteProduct(${p.id})">Delete</button>
            </td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    list.innerHTML = html;
}

function editProduct(id) {
    const p = products.find(prod => prod.id === id);
    if (!p) return;

    currentProductId = id;
    document.getElementById('new-product-name').value = p.product_name;
    document.getElementById('new-product-hsn').value = p.hsn || '';
    document.getElementById('new-product-price').value = p.default_price;
    document.getElementById('new-product-tax').value = p.default_tax;
    document.getElementById('new-product-unit').value = p.unit;

    // Change button text
    const btn = document.querySelector('#product-panel .btn-primary');
    if (btn) btn.textContent = 'Update Product';
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function addProductToCatalog() {
    const data = {
        product_name: document.getElementById('new-product-name').value,
        hsn: document.getElementById('new-product-hsn').value,
        default_price: parseFloat(document.getElementById('new-product-price').value) || 0,
        default_tax: parseFloat(document.getElementById('new-product-tax').value) || 0,
        unit: document.getElementById('new-product-unit').value || 'Nos'
    };
    
    if (!data.product_name) {
        showToast('Product name is required', true);
        return;
    }

    const method = currentProductId ? 'PUT' : 'POST';
    const url = currentProductId ? `/api/products/${currentProductId}` : '/api/products';
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(parseApiResponse)
    .then(() => {
        showToast(currentProductId ? 'Product updated' : 'Product added');
        resetProductForm();
        loadProducts();
    })
    .catch(err => showToast('Error saving product: ' + err.message, true));
}

function resetProductForm() {
    currentProductId = null;
    document.getElementById('new-product-name').value = '';
    document.getElementById('new-product-hsn').value = '';
    document.getElementById('new-product-price').value = '';
    document.getElementById('new-product-tax').value = '';
    document.getElementById('new-product-unit').value = 'Nos';
    const btn = document.querySelector('#product-panel .btn-primary');
    if (btn) btn.textContent = 'Add Product';
}

function deleteProduct(id) {
    if (!confirm('Delete this product?')) return;
    fetch(`/api/products/${id}`, { method: 'DELETE' })
        .then(parseApiResponse)
        .then(() => {
            showToast('Product deleted');
            loadProducts();
        })
        .catch(err => showToast('Error deleting product', true));
}


// ============================================================
// PRODUCT AUTOCOMPLETE — In-table search
// ============================================================
function handleProductSearch(input, rowIndex) {
    const query = input.value.trim();
    const wrapper = input.closest('.autocomplete-wrapper');
    let list = wrapper.querySelector('.autocomplete-list');
    
    if (query.length < 1) {
        list.classList.remove('show');
        return;
    }
    
    const matches = products.filter(p =>
        p.product_name.toLowerCase().includes(query.toLowerCase())
    );
    
    if (matches.length === 0) {
        list.classList.remove('show');
        return;
    }
    
    list.innerHTML = '';
    matches.forEach(p => {
        const div = document.createElement('div');
        div.className = 'ac-item';
        div.textContent = `${p.product_name} (HSN: ${p.hsn || '-'})`;
        div.addEventListener('click', function() {
            selectProductForRow(rowIndex, p);
            list.classList.remove('show');
        });
        list.appendChild(div);
    });
    list.classList.add('show');
}

function selectProductForRow(rowIndex, product) {
    const row = document.getElementById(`product-row-${rowIndex}`);
    if (!row) return;
    
    row.querySelector('.desc-input').value = product.product_name;
    row.querySelector('.hsn-input').value = product.hsn || '';
    row.querySelector('.rate-input').value = product.default_price || 0;
    row.querySelector('.per-input').value = product.unit || 'Nos';
    
    recalculate();
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('.autocomplete-wrapper')) {
        document.querySelectorAll('.autocomplete-list').forEach(l => l.classList.remove('show'));
    }
});


// ============================================================
// CUSTOMERS — Load, add, edit, delete, select
// ============================================================
function loadCustomers() {
    fetch('/api/customers')
        .then(parseApiResponse)
        .then(data => {
            customers = data;
            renderCustomerList();
            populateCustomerDropdown();
        })
        .catch(err => console.error('Error loading customers:', err));
}

function renderCustomerList() {
    const list = document.getElementById('customer-list');
    if (!list) return;
    
    if (customers.length === 0) {
        list.innerHTML = '<p style="color:#6b7280; font-size:13px;">No customers yet.</p>';
        return;
    }
    
    let html = `<table class="data-table">
        <thead><tr><th>Name</th><th>City</th><th>State</th><th>GSTIN</th><th>Action</th></tr></thead>
        <tbody>`;
    
    customers.forEach(c => {
        html += `<tr>
            <td>${c.customer_name}</td>
            <td>${c.city || '-'}</td>
            <td>${c.state_name || '-'}</td>
            <td>${c.gstin || '-'}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="editCustomer(${c.id})">Edit</button>
                <button class="btn btn-danger btn-sm" onclick="deleteCustomer(${c.id})">Delete</button>
            </td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    list.innerHTML = html;
}

function editCustomer(id) {
    const c = customers.find(cust => cust.id === id);
    if (!c) return;

    currentCustomerId = id;
    document.getElementById('new-cust-name').value = c.customer_name;
    document.getElementById('new-cust-address').value = c.address || '';
    document.getElementById('new-cust-city').value = c.city || '';
    document.getElementById('new-cust-state').value = c.state_name || '';
    document.getElementById('new-cust-gstin').value = c.gstin || '';
    document.getElementById('new-cust-phone').value = c.phone || '';
    document.getElementById('new-cust-email').value = c.email || '';

    const btn = document.querySelector('#customer-panel .btn-primary');
    if (btn) btn.textContent = 'Update Customer';
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function addCustomer() {
    const data = {
        customer_name: document.getElementById('new-cust-name').value,
        address: document.getElementById('new-cust-address').value,
        city: document.getElementById('new-cust-city').value,
        state_name: document.getElementById('new-cust-state').value,
        state_code: getStateCode(document.getElementById('new-cust-state').value),
        gstin: document.getElementById('new-cust-gstin').value,
        phone: document.getElementById('new-cust-phone').value,
        email: document.getElementById('new-cust-email').value
    };
    
    if (!data.customer_name) {
        showToast('Customer name is required', true);
        return;
    }

    const method = currentCustomerId ? 'PUT' : 'POST';
    const url = currentCustomerId ? `/api/customers/${currentCustomerId}` : '/api/customers';
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(parseApiResponse)
    .then(() => {
        showToast(currentCustomerId ? 'Customer updated' : 'Customer added');
        resetCustomerForm();
        loadCustomers();
    })
    .catch(err => showToast('Error saving customer', true));
}

function resetCustomerForm() {
    currentCustomerId = null;
    document.getElementById('new-cust-name').value = '';
    document.getElementById('new-cust-address').value = '';
    document.getElementById('new-cust-city').value = '';
    document.getElementById('new-cust-state').value = '';
    document.getElementById('new-cust-gstin').value = '';
    document.getElementById('new-cust-phone').value = '';
    document.getElementById('new-cust-email').value = '';
    const btn = document.querySelector('#customer-panel .btn-primary');
    if (btn) btn.textContent = 'Add Customer';
}

function deleteCustomer(id) {
    if (!confirm('Delete this customer?')) return;
    fetch(`/api/customers/${id}`, { method: 'DELETE' })
        .then(parseApiResponse)
        .then(() => {
            showToast('Customer deleted');
            loadCustomers();
        })
        .catch(err => showToast('Error deleting customer', true));
}

function populateCustomerDropdown() {
    const select = document.getElementById('customer-select');
    if (!select) return;
    select.innerHTML = '<option value="">-- Select Customer --</option>';
    customers.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.customer_name;
        select.appendChild(opt);
    });
}

function selectCustomer() {
    const select = document.getElementById('customer-select');
    const customerId = select.value;
    if (!customerId) return;
    const customer = customers.find(c => c.id == customerId);
    if (!customer) return;
    
    document.getElementById('ship-name').value = customer.customer_name || '';
    document.getElementById('ship-address').value = customer.address || '';
    document.getElementById('ship-gstin').value = customer.gstin || '';
    
    const shipState = document.getElementById('ship-state');
    if (shipState) {
        shipState.value = customer.state_name || '';
        updateStateCode('ship');
    }
    
    const sameCheckbox = document.getElementById('same-as-ship');
    if (sameCheckbox && sameCheckbox.checked) copyShipToBill();
}


// ============================================================
// SHIP TO / BILL TO TOGGLE
// ============================================================
function setupShipBillToggle() {
    const checkbox = document.getElementById('same-as-ship');
    if (checkbox) {
        checkbox.checked = true;
        checkbox.addEventListener('change', function() {
            if (this.checked) copyShipToBill();
        });
    }
}

function copyShipToBill() {
    document.getElementById('bill-name').value = document.getElementById('ship-name').value;
    document.getElementById('bill-address').value = document.getElementById('ship-address').value;
    document.getElementById('bill-gstin').value = document.getElementById('ship-gstin').value;
    if (document.getElementById('bill-state') && document.getElementById('ship-state')) {
        document.getElementById('bill-state').value = document.getElementById('ship-state').value;
        updateStateCode('bill');
    }
}

function onShipFieldChange() {
    const checkbox = document.getElementById('same-as-ship');
    if (checkbox && checkbox.checked) copyShipToBill();
}


// ============================================================
// STATE DROPDOWN — Auto-fill state code
// ============================================================
function getStateCode(stateName) {
    if (typeof INDIAN_STATES === 'undefined') return '';
    const state = INDIAN_STATES.find(s => s.name === stateName);
    return state ? state.code : '';
}

function updateStateCode(prefix) {
    const stateSelect = document.getElementById(`${prefix}-state`);
    const codeDisplay = document.getElementById(`${prefix}-state-code`);
    if (stateSelect && codeDisplay) {
        codeDisplay.textContent = getStateCode(stateSelect.value);
    }
}


// ============================================================
// PRODUCT TABLE ROWS
// ============================================================
let rowCounter = 0;

function addProductRow(shouldFocus = true) {
    rowCounter++;
    const tbody = document.getElementById('product-tbody');
    const slNo = tbody.querySelectorAll('tr.product-row').length + 1;

    const tr = document.createElement('tr');
    tr.id = `product-row-${rowCounter}`;
    tr.className = 'product-row';
    tr.innerHTML = `
        <td>
            <div class="row-sl-cell">
                <span class="sl-no">${slNo}</span>
                <span class="row-action-controls">
                    <button type="button" class="row-action-btn" onclick="addProductRow()" title="Add row">+</button>
                    <button type="button" class="row-action-btn" onclick="removeProductRow(${rowCounter})" title="Remove row">−</button>
                </span>
            </div>
        </td>
        <td class="text-left">
            <div class="autocomplete-wrapper">
                <input type="text" class="invoice-input desc-input" placeholder="Type product name..." oninput="handleProductSearch(this, ${rowCounter})" onchange="recalculate()">
                <div class="autocomplete-list"></div>
            </div>
        </td>
        <td><input type="text" class="invoice-input hsn-input" onchange="recalculate()"></td>
        <td>
            <div class="qty-controls">
                <button type="button" class="qty-btn" onclick="adjustQty(${rowCounter}, -1)">−</button>
                <input type="number" class="qty-input" value="0" min="0" onchange="recalculate()">
                <button type="button" class="qty-btn" onclick="adjustQty(${rowCounter}, 1)">+</button>
            </div>
        </td>
        <td>
            <div class="qty-controls">
                <button type="button" class="qty-btn" onclick="adjustRate(${rowCounter}, -1)">−</button>
                <input type="number" class="rate-input" value="0" step="0.01" onchange="recalculate()">
                <button type="button" class="qty-btn" onclick="adjustRate(${rowCounter}, 1)">+</button>
            </div>
        </td>
        <td>
            <select class="invoice-select per-input" onchange="recalculate()">
                <option value="Nos">Nos</option><option value="Pcs">Pcs</option><option value="Kg">Kg</option>
            </select>
        </td>
        <td><input type="number" class="invoice-input disc-input" value="0" step="0.01" onchange="recalculate()"></td>
        <td class="text-right amount-cell">0.00</td>
    `;

    tbody.appendChild(tr);
    renumberProductRows();
    applyRowReadonlyState(tr);
    if (shouldFocus && !isInvoiceReadOnly) tr.querySelector('.desc-input').focus();
}

function removeProductRow(rowId) {
    if (isInvoiceReadOnly) return;
    const rows = document.querySelectorAll('tr.product-row');
    if (rows.length <= 1) return;
    document.getElementById(`product-row-${rowId}`).remove();
    renumberProductRows();
    recalculate();
}

function renumberProductRows() {
    const rows = document.querySelectorAll('#product-tbody tr.product-row');
    rows.forEach((row, index) => {
        const slNoEl = row.querySelector('.sl-no');
        if (slNoEl) slNoEl.textContent = index + 1;
    });
}

function applyRowReadonlyState(row) {
    row.querySelectorAll('input, select').forEach(el => el.disabled = isInvoiceReadOnly);
    row.querySelectorAll('.qty-btn, .row-action-btn').forEach(btn => btn.style.display = isInvoiceReadOnly ? 'none' : 'inline-flex');
}

function setInvoiceReadOnly(readOnly) {
    isInvoiceReadOnly = readOnly;
    const panel = document.getElementById('invoice-panel');
    if (!panel) return;
    panel.querySelectorAll('input, select, textarea').forEach(el => el.disabled = readOnly);
    panel.querySelectorAll('tr.product-row').forEach(applyRowReadonlyState);
    const saveBtn = document.getElementById('save-invoice-btn');
    if (saveBtn) saveBtn.style.display = readOnly ? 'none' : 'inline-block';
}

function adjustQty(rowId, delta) {
    const input = document.getElementById(`product-row-${rowId}`).querySelector('.qty-input');
    input.value = Math.max(0, (parseFloat(input.value) || 0) + delta);
    recalculate();
}

function adjustRate(rowId, delta) {
    const input = document.getElementById(`product-row-${rowId}`).querySelector('.rate-input');
    input.value = Math.max(0, (parseFloat(input.value) || 0) + delta);
    recalculate();
}


// ============================================================
// CALCULATIONS
// ============================================================
function recalculate() {
    const rows = document.querySelectorAll('tr.product-row');
    let subtotal = 0;
    let totalQty = 0;
    
    rows.forEach(row => {
        const qty = parseFloat(row.querySelector('.qty-input').value) || 0;
        const rate = parseFloat(row.querySelector('.rate-input').value) || 0;
        const disc = parseFloat(row.querySelector('.disc-input').value) || 0;
        let amount = qty * rate;
        if (disc > 0) amount -= (amount * disc / 100);
        row.querySelector('.amount-cell').textContent = amount.toFixed(2);
        subtotal += amount;
        totalQty += qty;
    });
    
    document.getElementById('total-qty').textContent = totalQty;
    document.getElementById('subtotal-amount').textContent = subtotal.toFixed(2);
    
    const taxType = document.querySelector('input[name="tax-type"]:checked');
    let taxRate = (taxType && taxType.value === 'custom') ? parseFloat(document.getElementById('custom-tax-rate').value) || 0 : 12;
    if (taxType && taxType.value === 'none') taxRate = 0;
    
    const taxAmount = subtotal * taxRate / 100;
    const grandTotal = subtotal + taxAmount;
    
    document.getElementById('tax-amount-display').textContent = taxAmount.toFixed(2);
    document.getElementById('grand-total-display').textContent = '₹ ' + grandTotal.toFixed(2);
    
    updateTaxSummary(subtotal, taxRate, taxAmount, taxType ? taxType.value : 'igst');
    updateAmountWords(grandTotal, taxAmount);
}

function updateTaxSummary(subtotal, taxRate, taxAmount, taxType) {
    const tbody = document.getElementById('tax-summary-tbody');
    if (!tbody) return;
    
    const hsnMap = {};
    document.querySelectorAll('tr.product-row').forEach(row => {
        const hsn = row.querySelector('.hsn-input').value || '-';
        const amount = parseFloat(row.querySelector('.amount-cell').textContent) || 0;
        if (amount > 0) hsnMap[hsn] = (hsnMap[hsn] || 0) + amount;
    });
    
    let html = '';
    Object.keys(hsnMap).forEach(hsn => {
        const taxable = hsnMap[hsn];
        const tax = taxable * taxRate / 100;
        html += `<tr><td>${hsn}</td><td>${taxable.toFixed(2)}</td><td>${taxRate}%</td><td>${tax.toFixed(2)}</td><td>${tax.toFixed(2)}</td></tr>`;
    });
    
    tbody.innerHTML = html;
}

function updateAmountWords(grandTotal, taxAmount) {
    fetch(`/api/number-to-words?amount=${grandTotal}`).then(r => r.json()).then(data => {
        const el = document.getElementById('amount-words');
        if (el) el.textContent = data.words;
    });
}


// ============================================================
// TAX SELECTOR
// ============================================================
function setupTaxSelector() {
    document.querySelectorAll('input[name="tax-type"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const wrapper = document.getElementById('custom-tax-wrapper');
            if (wrapper) wrapper.style.display = this.value === 'custom' ? 'inline-flex' : 'none';
            recalculate();
        });
    });
}


// ============================================================
// INVOICE NUMBER & DATE
// ============================================================
function fetchNextInvoiceNumber() {
    fetch('/api/invoices/next-number').then(parseApiResponse).then(data => {
        document.getElementById('invoice-no').value = data.invoice_no;
    });
}

function setDefaultDateTime() {
    const dateInput = document.getElementById('invoice-date');
    if (dateInput) dateInput.value = new Date().toISOString().slice(0, 16);
}


// ============================================================
// SAVE INVOICE
// ============================================================
function collectInvoicePayload() {
    const items = [];
    document.querySelectorAll('tr.product-row').forEach(row => {
        const desc = row.querySelector('.desc-input').value;
        if (desc.trim()) {
            items.push({
                sl_no: items.length + 1,
                description: desc,
                hsn: row.querySelector('.hsn-input').value,
                quantity: parseFloat(row.querySelector('.qty-input').value) || 0,
                rate: parseFloat(row.querySelector('.rate-input').value) || 0,
                per_unit: row.querySelector('.per-input').value,
                discount_percent: parseFloat(row.querySelector('.disc-input').value) || 0,
                amount: parseFloat(row.querySelector('.amount-cell').textContent) || 0
            });
        }
    });

    if (items.length === 0) throw new Error('Add at least one product');

    return {
        invoice_id: currentInvoiceId,
        invoice_no: document.getElementById('invoice-no').value,
        invoice_date: document.getElementById('invoice-date').value,
        buyer_name: document.getElementById('bill-name').value,
        buyer_address: document.getElementById('bill-address').value,
        buyer_state: document.getElementById('bill-state')?.value || '',
        buyer_state_code: document.getElementById('bill-state-code')?.textContent || '',
        buyer_gstin: document.getElementById('bill-gstin').value,
        ship_to_name: document.getElementById('ship-name').value,
        ship_to_address: document.getElementById('ship-address').value,
        ship_to_state: document.getElementById('ship-state')?.value || '',
        ship_to_state_code: document.getElementById('ship-state-code')?.textContent || '',
        ship_to_gstin: document.getElementById('ship-gstin').value,
        delivery_note: document.getElementById('delivery-note').value,
        payment_mode: document.getElementById('payment-mode').value,
        reference_no: document.getElementById('reference-no').value,
        other_references: document.getElementById('other-ref').value,
        buyer_order_no: document.getElementById('buyer-order-no').value,
        buyer_order_date: document.getElementById('buyer-order-date').value,
        dispatch_doc_no: document.getElementById('dispatch-doc-no').value,
        delivery_note_date: document.getElementById('delivery-note-date').value,
        dispatched_through: document.getElementById('dispatched-through').value,
        destination: document.getElementById('destination').value,
        terms_of_delivery: document.getElementById('terms-delivery').value,
        tax_type: document.querySelector('input[name="tax-type"]:checked')?.value || 'igst',
        custom_tax_rate: parseFloat(document.getElementById('custom-tax-rate').value) || 0,
        subtotal: parseFloat(document.getElementById('subtotal-amount').textContent) || 0,
        tax_amount: parseFloat(document.getElementById('tax-amount-display').textContent) || 0,
        grand_total: parseFloat(document.getElementById('grand-total-display').textContent.replace(/[^0-9.-]/g, '')) || 0,
        items
    };
}

function saveInvoice(showSuccessToast = true) {
    let data;
    try { data = collectInvoicePayload(); } catch (err) { showToast(err.message, true); return Promise.reject(err); }

    return fetch('/api/invoices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(parseApiResponse)
    .then(result => {
        currentInvoiceId = result.invoice_id || currentInvoiceId;
        if (showSuccessToast) showToast(`Invoice ${result.mode === 'updated' ? 'updated' : 'saved'} successfully`);
        loadSavedInvoices();
        return result;
    })
    .catch(err => { showToast('Error saving invoice', true); throw err; });
}


// ============================================================
// SAVED INVOICES
// ============================================================
function loadSavedInvoices() {
    fetch('/api/invoices').then(parseApiResponse).then(invoices => {
        const list = document.getElementById('saved-invoices-list');
        if (!list) return;
        if (invoices.length === 0) { list.innerHTML = '<p>No saved invoices.</p>'; return; }
        let html = '';
        invoices.forEach(inv => {
            html += `<div class="invoice-list-item">
                <div class="inv-info"><span class="inv-no">${inv.invoice_no}</span><span class="inv-detail">${inv.buyer_name || 'No buyer'}</span></div>
                <span class="inv-amount">₹${parseFloat(inv.grand_total).toFixed(2)}</span>
                <div class="inv-actions">
                    <button class="btn btn-secondary btn-sm" onclick="loadInvoice(${inv.id}, true)">View</button>
                    <button class="btn btn-primary btn-sm" onclick="loadInvoice(${inv.id}, false)">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteInvoice(${inv.id})">Delete</button>
                </div>
            </div>`;
        });
        list.innerHTML = html;
    });
}

function loadInvoice(id, readOnly = false) {
    fetch(`/api/invoices/${id}`).then(parseApiResponse).then(inv => {
        currentInvoiceId = inv.id;
        switchToPanel('invoice-panel');
        document.getElementById('invoice-no').value = inv.invoice_no || '';
        document.getElementById('invoice-date').value = inv.invoice_date || '';
        document.getElementById('bill-name').value = inv.buyer_name || '';
        document.getElementById('bill-address').value = inv.buyer_address || '';
        document.getElementById('bill-gstin').value = inv.buyer_gstin || '';
        if (document.getElementById('bill-state')) {
            document.getElementById('bill-state').value = inv.buyer_state || '';
            updateStateCode('bill');
        }
        
        const tbody = document.getElementById('product-tbody');
        tbody.innerHTML = ''; rowCounter = 0;
        inv.items.forEach(item => {
            addProductRow(false);
            const row = document.getElementById(`product-row-${rowCounter}`);
            row.querySelector('.desc-input').value = item.description;
            row.querySelector('.hsn-input').value = item.hsn;
            row.querySelector('.qty-input').value = item.quantity;
            row.querySelector('.rate-input').value = item.rate;
            row.querySelector('.per-input').value = item.per_unit;
            row.querySelector('.disc-input').value = item.discount_percent;
        });
        recalculate();
        setInvoiceReadOnly(readOnly);
    });
}

function deleteInvoice(id) {
    if (!confirm('Delete this invoice?')) return;
    fetch(`/api/invoices/${id}`, { method: 'DELETE' }).then(() => { showToast('Invoice deleted'); loadSavedInvoices(); });
}


// ============================================================
// PRINT & PDF
// ============================================================
function printInvoice() { window.print(); }

function downloadPDF() {
    showToast('Generating PDF...');
    saveInvoice(false).then(result => {
        window.open(`/api/invoices/${result.invoice_id || currentInvoiceId}/pdf`, '_blank');
    });
}


// ============================================================
// NEW INVOICE — Reset form
// ============================================================
function newInvoice() {
    currentInvoiceId = null;
    setInvoiceReadOnly(false);
    document.querySelectorAll('#invoice-panel input, #invoice-panel textarea').forEach(el => el.value = '');
    document.getElementById('product-tbody').innerHTML = ''; rowCounter = 0;
    addProductRow(false);
    fetchNextInvoiceNumber();
    setDefaultDateTime();
    recalculate();
    switchToPanel('invoice-panel');
}


// ============================================================
// TOAST NOTIFICATION
// ============================================================
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast show' + (isError ? ' error' : '');
    setTimeout(() => toast.className = 'toast', 3000);
}