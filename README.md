# FastAPI E-Commerce API 🚀

A modern, fast, and robust E-Commerce API built with Python, FastAPI, and SQLAlchemy. This project demonstrates layered architecture, JWT authentication, role-based access control (RBAC), Pydantic v2 validation, and transactional order processing.

## Features ✨

*   **FastAPI:** High-performance REST API with automatic OpenAPI/Swagger UI documentation.
*   **SQLAlchemy 2.0:** Relational database modeling with PostgreSQL (production) and SQLite (local/test) support, `Numeric(10, 2)` monetary precision, and atomic order transactions.
*   **Authentication & RBAC:** Secure JWT authentication (`python-jose`), direct `bcrypt` password hashing, active-user checks, and admin-only (`is_superuser`) product creation.
*   **Pydantic v2:** Strict input validation, email normalization, and environment-based settings management (`pydantic-settings`).
*   **Layered Architecture:** Clean separation between API routers (`api/`), database operations (`crud/`), ORM models (`models/`), and Pydantic schemas (`schemas/`).

## Tech Stack 🛠️

*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **Database:** PostgreSQL / SQLite
*   **ORM:** SQLAlchemy 2.0
*   **Data Validation:** Pydantic v2 & Pydantic Settings
*   **Authentication:** Bcrypt, Python-Jose (JWT)
*   **Server:** Uvicorn
*   **Testing:** Pytest, HTTPX (`TestClient`)

## Project Structure 📁

```text
ecommerce-api/
│
├── api/                 # API Routers and Dependencies
│   ├── endpoints/       # Route definitions (auth, products, orders)
│   └── deps.py          # Auth & RBAC dependencies (get_current_active_user, get_current_admin_user)
├── core/                # Core configuration, DB, and security
│   ├── config.py        # Environment-backed application settings
│   ├── database.py      # SQLAlchemy engine, SessionLocal, Base, get_db
│   └── security.py      # Bcrypt hashing and JWT token creation
├── crud/                # Database CRUD operations
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic v2 request/response schemas
├── tests/               # Pytest automated test suite
├── .env.example         # Example environment variables template
├── main.py              # Application entry point, lifespan, CORS, healthcheck
├── requirements.txt     # Runtime dependencies
└── requirements-dev.txt # Runtime + test dependencies
```

## How to Run Locally 💻

1. **Clone the repository**
   ```bash
   git clone https://github.com/KenanToprak/ecommerce-api.git
   cd ecommerce-api
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv .venv
   # On Windows:
   .\.venv\Scripts\activate
   # On Linux/Mac:
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure Environment Variables**
   Copy `.env.example` to `.env` and update the values (never commit `.env` or hardcode secrets in source files):
   ```bash
   cp .env.example .env
   ```
   *   `DATABASE_URL`: Defaults to local SQLite (`sqlite:///./ecommerce.db`) if omitted. Set a PostgreSQL connection string for production.
   *   `SECRET_KEY`: Set a strong random secret key in `.env` (if omitted, an ephemeral random key is generated at startup with a warning).
   *   `CORS_ORIGINS`: JSON array of allowed origins.

5. **Run the Application**
   ```bash
   uvicorn main:app --reload
   ```

6. **Explore the API**
   *   Swagger UI: `http://127.0.0.1:8000/docs`
   *   Healthcheck: `http://127.0.0.1:8000/health`

## API Endpoints & Roles 🔐

*   `GET /` — API welcome message
*   `GET /health` — Database connectivity healthcheck
*   `POST /auth/register` — Register a regular user (`is_active=True`, `is_superuser=False`)
*   `POST /auth/login` — OAuth2 password flow login (`username` = email) returning a Bearer JWT
*   `GET /products/` — List products (`skip >= 0`, `1 <= limit <= 100`)
*   `GET /products/{product_id}` — Get product details
*   `POST /products/` — Create a product (**admin only**: requires `is_superuser=True`)
*   `POST /orders/` — Create an order atomically (**authenticated active user**)
*   `GET /orders/my-orders` — List the authenticated user's orders (`skip >= 0`, `1 <= limit <= 100`)

## Running Tests 🧪

The test suite uses an isolated in-memory SQLite database and does not require a running PostgreSQL server:

```bash
pytest -v
```

## License 📝
MIT
