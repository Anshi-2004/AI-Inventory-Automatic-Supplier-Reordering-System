# 🚀 How to Run the AI Smart Inventory & Order Management System

This guide provides complete, step-by-step instructions to set up, configure, and run both the **Backend (FastAPI)** and **Frontend (React + Vite)** applications locally.

---

## 📋 Prerequisites

Ensure you have the following installed on your machine:
* **Python** 3.10+ (Python 3.12 recommended)
* **Node.js** 18+ (Node.js 20 recommended) & `npm`
* **Git** (optional)

---

## ⚙️ Step 1: Backend Setup (FastAPI)

1. **Open a terminal** and navigate to the `backend` directory:
   ```bash
   cd "c:\Users\anshi\OneDrive\Desktop\Power BI\order_management\backend"
   ```

2. **Create and Activate a Python Virtual Environment**:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   * **Windows (Command Prompt)**:
     ```cmd
     python -m venv .venv
     .\.venv\Scripts\activate.bat
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt aiosqlite email-validator
   ```

4. **Configure Environment Variables (`.env`)**:
   Ensure `.env` exists in the `backend` folder and contains the **SQLite database URL**:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./inventory.db
   JWT_SECRET=change-me-to-a-very-long-random-secret-string
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=1440
   APP_ENV=development
   FRONTEND_URL=http://localhost:5173
   BACKEND_PORT=8000
   ```
   > ⚠️ **Important**: Ensure `DATABASE_URL` uses `sqlite+aiosqlite:///./inventory.db` unless you are actively running a local PostgreSQL service.

5. **Seed Initial Data (Optional / Fresh Setup)**:
   If you need to populate default products, suppliers, alerts, and user accounts:
   ```bash
   python scripts/seed_data.py
   ```

6. **Start the Backend Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
   * Backend REST API: [http://localhost:8000](http://localhost:8000)
   * Interactive API Documentation (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
   * System Health Endpoint: [http://localhost:8000/health](http://localhost:8000/health)

---

## 💻 Step 2: Frontend Setup (React + Vite)

1. **Open a new terminal window** and navigate to the `frontend` directory:
   ```bash
   cd "c:\Users\anshi\OneDrive\Desktop\Power BI\order_management\frontend"
   ```

2. **Install Node Package Dependencies**:
   ```bash
   npm install
   ```

3. **Start the Frontend Development Server**:
   ```bash
   npm run dev
   ```
   * Application UI URL: [http://localhost:5173](http://localhost:5173)

---

## 🔑 Demo Credentials

Use these pre-seeded accounts to log in on the frontend:

| Role | Email Address | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@inventory.com` | `Admin@1234` | Full access (Users, Inventory, Orders, Approvals) |
| **Inventory Manager** | `manager@inventory.com` | `Manager@1234` | Inventory, Stock Tracking, Order Requests |

---

## ❓ Troubleshooting & FAQs

### Q: Why does the UI show "Login failed. Check your credentials."?
* **Cause**: The backend server is returning an HTTP 500 error because `DATABASE_URL` in `backend/.env` is set to PostgreSQL instead of local SQLite.
* **Fix**: Ensure `DATABASE_URL=sqlite+aiosqlite:///./inventory.db` is present in `backend/.env` and save the file to trigger a server reload.

### Q: Port 8000 or 5173 is already in use
* **Fix**: Change `BACKEND_PORT` in `backend/.env` or specify a custom port when starting uvicorn:
  ```bash
  uvicorn app.main:app --reload --port 8005
  ```

---

## 🐳 Optional: Running via Docker Compose

If Docker Desktop is installed, you can launch both services together with one command:
```bash
docker-compose up --build
```
* Frontend: `http://localhost:5173`
* Backend API Docs: `http://localhost:8000/docs`
