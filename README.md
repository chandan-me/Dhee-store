# Dhee Stores - Layered FastAPI MySQL Microservices & React Platform

A production-grade, distributed e-commerce microservices platform built with **Python 3 (FastAPI)**, **MySQL 8.0**, and **React 18 (Vite)**. The architecture features an intelligent API Gateway with direct reverse proxy routing, JWT gatekeeper security, dynamic database authentication with Bcrypt hashing, per-service isolated databases, distributed saga transactions for multi-item cart checkout, Razorpay and COD payment processing, and an interactive business analytics dashboard.

> [!NOTE]
> For complete visual sequence diagrams of all transaction flows (registration, shopping cart checkout, Razorpay verification, administrative block controls, and data federation), refer to [ARCHITECTURE.md](file:///c:/Users/user/Downloads/microservices/docs/ARCHITECTURE.md).

---


---

## 🧭 Service Port Directory

| Component | Port | Base URL | Interactive Docs (Swagger) | Database | Primary Responsibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **API Gateway** | `8010` | `http://127.0.0.1:8010` | `http://127.0.0.1:8010/docs` | Stateless / JWT | Single Entrypoint, JWT Validation, RBAC, Reverse Proxy |
| **User Service** | `8011` | `http://127.0.0.1:8011` | `http://127.0.0.1:8011/docs` | MySQL: `users_db` | User Identity, Bcrypt Passwords, Token Persistence, Soft Block |
| **Product Service** | `8012` | `http://127.0.0.1:8012` | `http://127.0.0.1:8012/docs` | MySQL: `products_db` | Merchandise Catalog, Pricing, Stock Management, Product Block |
| **Order Service** | `8013` | `http://127.0.0.1:8013` | `http://127.0.0.1:8013/docs` | MySQL: `orders_db` | Saga Orchestration, Cart Checkout, COD & Razorpay Processing |
| **React Frontend** | `5173` | `http://localhost:5173` | N/A (Web UI) | Browser LocalStorage | Modern Shopping UI, Cart Steppers, Analytics & Order Bundles |

---

## 📂 Project Directory Structure

```
microservices/
├── .env                         # Central configuration, MySQL credentials & Razorpay keys
├── .env.example                 # Template for local environment setup
├── .gitignore                   # Ignored files (logs, caches, build artifacts, lock files)
├── db_setup.sql                 # Official MySQL schema initialization & seed script
├── README.md                    # Project manual & documentation
├── requirements.txt             # Python backend dependencies
├── run_all.py                   # Master process runner for all 5 services
│
├── docs/                        # Architectural documentation
│   ├── ARCHITECTURE.docx        # Word document system reference
│   └── ARCHITECTURE.md          # Visual sequence diagrams & data travel manual
│
├── gateway_service/             # API Gateway (Port 8010)
│   ├── auth.py                  # JWT encoding, decoding, and expiration handling
│   └── main.py                  # Direct reverse proxy, whitelist, and RBAC filters
│
├── user_service/                # User Domain Microservice (Port 8011)
│   ├── database.py              # PyMySQL engine setup & SessionLocal dependency
│   ├── models.py                # SQLAlchemy ORM model ('users' table)
│   ├── schemas.py               # Pydantic validation schemas
│   └── main.py                  # User management, Bcrypt hashing, token persistence
│
├── product_service/             # Product Domain Microservice (Port 8012)
│   ├── database.py              # PyMySQL engine setup & SessionLocal dependency
│   ├── models.py                # SQLAlchemy ORM model ('products' table)
│   ├── schemas.py               # Pydantic validation schemas
│   └── main.py                  # Catalog endpoints, search/filtering, atomic stock deduction
│
├── order_service/               # Order Domain Microservice (Port 8013)
│   ├── database.py              # PyMySQL engine setup & SessionLocal dependency
│   ├── models.py                # SQLAlchemy ORM model ('orders' table)
│   ├── schemas.py               # Pydantic validation schemas
│   └── main.py                  # Distributed saga, multi-item checkout, Razorpay & COD
│
└── frontend/                    # Single-Page Application (React 18 + Vite)
    ├── package.json             # Frontend dependencies & scripts
    ├── vite.config.js           # Vite dev server configuration
    ├── public/
    │   └── logo.png             # Application logo
    └── src/
        ├── App.jsx              # Main React state coordinator & view router
        ├── index.css            # Custom responsive stylesheet & modern scrollbars
        ├── main.jsx             # React DOM entrypoint
        ├── components/
        │   ├── AdminDashboard.jsx # Analytics dashboard, pie chart, stock status table
        │   ├── AuthScreen.jsx     # Login & registration screen (Formik + Yup)
        │   ├── CartPage.jsx       # Dedicated multi-item shopping cart page
        │   ├── Navbar.jsx         # Responsive top navigation & avatar dropdown
        │   ├── OrdersPage.jsx     # Consolidated order bundle history page
        │   ├── ProductCard.jsx    # Product display card with inline quantity steppers
        │   ├── ProductModal.jsx   # Admin Add/Edit product modal
        │   ├── ProfileModal.jsx   # User profile management & avatar URL update
        │   └── UsersModal.jsx     # Admin registered users directory
        ├── services/
        │   └── api.js           # Centralized API service layer communicating with Gateway
        └── utils/
            └── format.js        # Thousands comma separator formatters (formatCurrency, formatNumber)
```

---

## 🚀 Quickstart Guide (For You & Friends)

### 1. Prerequisites
- **Python**: Version 3.10 or higher.
- **Node.js**: Version 18.0 or higher (with `npm`).
- **MySQL Community Server**: Installed and running on `localhost:3306`.
  *(Make sure the MySQL service is started via Windows Services or `Start-Service MySQL80`).*

---

### 2. Configure Environment (`.env`)
When you clone the repository, create a `.env` file at the root (or let `run_all.py` auto-generate it for you):

```env
# MySQL Connection Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_mysql_root_password

# JWT Security
JWT_SECRET=demo_secret_key_Demo_gatekeeper_auth_2026
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=300000

# Razorpay Payment Gateway (Test keys included)
RAZORPAY_KEY_ID=rzp_test_T9pQXLodEsWanv
RAZORPAY_KEY_SECRET=fe8EIlYB67kM4aLCqcn09YSX
```

> [!IMPORTANT]
> Be sure to set `MYSQL_PASSWORD` to your local MySQL root password! If left blank and your MySQL requires a password, backend services will not be able to connect.

---

### 3. Install Dependencies

#### Python Packages
```powershell
pip install -r requirements.txt
```

#### Frontend Packages
```powershell
npm --prefix frontend install
```

---

### 4. Zero-Setup Database Initialization
> [!TIP]
> You **do not** need to manually create databases! `run_all.py` and each microservice will **automatically create** `users_db`, `products_db`, and `orders_db` and seed default users and catalog products on first launch.
>
> *(Optional)*: If you ever want to reset all tables and sample records manually:
> ```powershell
> mysql -u root -p < db_setup.sql
> ```

---

### 5. Launch the Entire System
Start all 3 Microservices, the API Gateway, and the React Frontend with a single command:

```powershell
python run_all.py
```

`run_all.py` runs automated pre-flight checks:
- Verifies MySQL is running and reachable on port 3306.
- Tests your MySQL credentials and auto-creates the databases if they don't exist.
- Starts all microservices and monitors for any startup errors.

When ready, open your browser:
- **🛍️ React Application UI**: [http://localhost:5173](http://localhost:5173)
- **🛡️ API Gateway Swagger Docs**: [http://127.0.0.1:8010/docs](http://127.0.0.1:8010/docs)

**Default Login Accounts:**
- **Admin**: `admin@store.com` / `admin123`
- **Customer**: `customer@store.com` / `customer123`

*(Press `Ctrl+C` in the terminal to gracefully terminate all services).*


---

## 🔑 Key Features & Architectural Capabilities

### 1. Dynamic Database Authentication (Zero Hardcoding)
- All user credentials, accounts, and passwords are dynamically read and validated against MySQL `users_db.users`.
- Passwords are encrypted using modern **Bcrypt** hashing (`$2b$12$...`).
- Persists active JWT access tokens, expiration dates, and last login timestamps into the database upon successful authentication.
- Supports custom user avatar photos via `profile_image` URLs rendered in the navbar and profile modal.

### 2. Administrative Soft Block / Unblock System
- Replaces destructive deletions with an administrative soft-block flag (`is_blocked TINYINT(1) DEFAULT 0`):
  - **User Blocking**: Blocks malicious accounts without data loss. Blocked users are immediately logged out and rejected with `403 Forbidden`.
  - **Product Blocking**: Blocks discontinued or out-of-stock items. Blocked products display a `🚫 Item Blocked` badge and are blocked from cart checkout.
  - Admins can toggle block and unblock statuses with one click in the UI.

### 3. Multi-Item Shopping Cart with In-Card Steppers
- Customers can add products to cart directly from catalog cards with instant `[-] quantity [+]` stepper controls.
- The dedicated **Shopping Cart Page** supports multi-item checkout in a single session.
- Purchases with multiple distinct items are automatically bundled into **ONE consolidated Order Card** in "My Orders", itemizing product details, unit prices, line totals, and grand total.

### 4. Dual Payment Processing (COD & Razorpay)
- **Cash on Delivery (COD)**: Immediately confirms and fulfills orders upon checkout.
- **Razorpay Online Payments**:
  - Dynamically creates Razorpay orders via `POST /orders/payment/razorpay/order`.
  - Opens the secure Razorpay Checkout popup with live currency conversion.
  - Verifies payment authenticity via server-side HMAC SHA-256 signature checking (`POST /orders/payment/razorpay/verify`).

### 5. Symmetrical 50/50 Admin Business Analytics Dashboard
- **Top Metrics Cards**: Real-time Total Sales (`₹`), Total Orders Placed, Inventory Retail Value, and Registered User Counts.
- **Left Card — Sales Distribution Donut Chart**: Interactive SVG donut pie chart showing revenue share and units sold per product with interactive tooltips and legend.
- **Right Card — Catalog Stock & Cost Status**: Equal 50/50 split table with aligned column metrics (`Product`, `Status` pill badges, right-aligned `Price`, centered `Stock`, right-aligned `Total Valuation`).

### 6. Number & Currency Formatting
- Standardized to Indian Rupee (**`₹`**).
- Thousands comma separation applied to all currency and quantity values &ge; 1,000 (e.g. `₹1,099.99`, `1,000 units`, `₹610,011.47`).
