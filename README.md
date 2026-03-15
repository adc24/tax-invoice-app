# Tax Invoice – Billing Application 🚀

**Tax Invoice** is a professional, full-stack SaaS-style billing system designed for Indian businesses. Built with **Python Flask** and **SQLite**, the application automates the process of generating **GST-compliant tax invoices** with a clean, pixel-perfect **A4 printable layout** suitable for printing or PDF export.

The system simplifies invoice management by automating invoice numbering, GST calculations, currency-to-words conversion, and invoice generation — all within a simple web interface.

---

# 🌟 Key Features

## Smart Automation

### Auto-Incrementing Invoices

Automatically generates the next invoice number (for example: `INV-0034`).
Manual overrides are also supported if the user needs to create a custom invoice number.

### Automatic State Fetching

Select any of the **37 Indian States and Union Territories** to instantly fetch the correct **GST State Code**.

Examples:

| State         | GST Code |
| ------------- | -------- |
| Karnataka     | 29       |
| Maharashtra   | 27       |
| Uttar Pradesh | 09       |

---

## Intelligent Business Logic

### Currency-to-Words Conversion

Automatically converts the **Grand Total** and **Tax Amounts** into **Indian Rupee words**, including correct **Paise formatting**.

Example:

```
₹12,450.50
Twelve Thousand Four Hundred Fifty Rupees and Fifty Paise Only
```

This functionality is powered by the **num2words** Python library using the **Indian English locale**.

---

### Live GST Calculation

Supports both GST tax structures used in India:

• **IGST** (Inter-State transactions)
• **CGST + SGST** (Intra-State transactions)

Switching between tax types instantly recalculates:

* Item totals
* Subtotal
* Tax amount
* Grand total

All calculations are handled dynamically using JavaScript.

---

# 🧾 Professional Invoice Output

### A4 Optimized Layout

Custom CSS ensures that invoices are **perfectly formatted for A4 printing**.

Benefits:

* Fits on a single page
* Clean spacing
* Professional formatting
* Compatible with printers and PDF export

---

### PDF Generation

Invoices can be exported as professional PDF files using **WeasyPrint**.

Advantages:

* Keeps exact HTML styling
* Supports modern CSS
* Produces high-quality print-ready invoices

---

### Dynamic Authorized Signatory

The **Authorized Signatory** field automatically updates with the **business name**, giving the invoice a professional appearance.

---

# 📊 Data Management

The system includes full **CRUD operations** for managing business data.

## Customers

Users can:

* Add new customers
* Edit customer details
* Delete customers
* Store GSTIN, address, phone, and other information

---

## Products

Users can:

* Add products
* Edit product pricing
* Delete products
* Store units and tax information

---

## Invoices

Users can:

* Create invoices
* Print invoices
* Download invoices as PDF
* Automatically calculate totals and taxes

---

# 🛠️ Technology Stack

| Category          | Technology                      |
| ----------------- | ------------------------------- |
| Backend           | Python 3.x                      |
| Framework         | Flask                           |
| Database          | SQLite3                         |
| Frontend          | HTML5, CSS3, Vanilla JavaScript |
| PDF Engine        | WeasyPrint                      |
| Utility Libraries | num2words                       |
| Deployment        | Railway.app                     |
| Version Control   | GitHub                          |

---

# 📂 Project Structure

```
tax-invoice-app/
│
├── data/                         # SQLite database storage
│
├── static/
│   ├── css/
│   │   └── style.css             # Main stylesheet and A4 print layout
│   │
│   └── js/
│       └── invoice.js            # Calculation engine and frontend logic
│
├── templates/
│   ├── invoice.html              # Main dashboard / invoice creation UI
│   └── invoice_print.html        # Template used for printing and PDF export
│
├── main.py                       # Flask application and API routes
├── requirements.txt              # Python dependencies
└── Procfile                      # Railway deployment configuration
```

---

# ⚙️ Installation (Local Development)

## 1️⃣ Clone the Repository

```
git clone https://github.com/yourusername/tax-invoice-app.git
cd tax-invoice-app
```

---

## 2️⃣ Create Virtual Environment

```
python -m venv venv
```

Activate the environment.

### Windows

```
venv\Scripts\activate
```

### Mac / Linux

```
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

## 4️⃣ Run the Application

```
python main.py
```

The application will start at:

```
http://127.0.0.1:5000
```

Open this address in your browser.

---

# 🚀 Deployment (Railway)

This project can be deployed easily using **Railway.app**.

### Deployment Steps

1. Push the project to GitHub
2. Open Railway
3. Click **New Project**
4. Select **Deploy from GitHub Repository**
5. Choose this repository
6. Railway will automatically detect the Python environment and deploy

---

### Procfile Configuration

The Procfile used for deployment:

```
web: gunicorn main:app
```

This tells Railway to run the Flask application using **Gunicorn**.

---

# 📄 PDF Generation

Invoices can be downloaded as PDFs using **WeasyPrint**.

Workflow:

```
HTML Invoice Template
        ↓
WeasyPrint Engine
        ↓
Generated PDF File
        ↓
User Download
```

This ensures the **PDF layout matches the HTML design exactly**.

---

# 🔮 Future Improvements

Planned improvements for future versions include:

* User authentication system
* Multi-user SaaS billing system
* Cloud database support (PostgreSQL / MySQL)
* Invoice dashboard analytics
* Inventory management
* GST reporting tools
* Email invoice sending
* Company profile management
* Multiple business support

---

# 🤝 Contributing

Contributions are welcome.

To contribute:

1. Fork the repository
2. Create a new branch
3. Submit a pull request

Bug reports and feature suggestions are also appreciated.

---

# 📜 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Author

Developed by **Abhay Chouhan**

If you find this project helpful, please ⭐ the repository on GitHub.
