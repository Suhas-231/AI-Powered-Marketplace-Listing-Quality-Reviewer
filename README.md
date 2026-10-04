# Marketplace Listing Quality Reviewer

A complete, production-oriented full-stack application built with **React**, **Flask**, **MySQL**, and **Groq API** (`groq` SDK) to audit product and service listings against marketplace policies, identify non-compliant claims, and streamline human-in-the-loop content revision.

---

## 1. Project Overview

E-commerce marketplaces face significant risks from misleading promotional superlatives, unverified medical/health promises, prohibited items, off-platform redirects, and counterfeit trademark violations. 

The **Marketplace Listing Quality Reviewer** acts as an automated compliance co-pilot:
1. Performs deterministic schema, price, category, and duplicate validation.
2. Dynamically retrieves relevant demonstration policies from a MySQL knowledge base.
3. Submits listings to Groq API (`openai/gpt-oss-20b`) with structured JSON schema constraints.
4. Verifies cited policy sections against real database records to prevent LLM hallucination.
5. Implements a human-in-the-loop workflow (**Approve**, **Edit**, **Reject**) where revisions are only applied to listings upon explicit user confirmation.
6. Maintains a persistent, tamper-evident audit log of all compliance decisions.

> [!NOTE]
> **Demonstration Knowledge Base Notice:** This application includes a demonstration policy knowledge base containing clearly labeled sample policies. It clearly distinguishes sample demonstration rules from official verified enterprise policies.

---

## 2. Key Features

- **Executive Quality Dashboard**: Real-time summary KPI cards, severity distribution breakdown (High: Red, Medium: Amber, Low: Blue), recent reviews, and recent human approval decisions.
- **Deterministic Validation Engine**: Python-based validation enforcing required fields, positive numeric prices, category whitelisting, title/description character limits, and duplicate title detection.
- **AI Compliance Agent**: Integrated via the official Groq Python SDK (`groq`), generating structured findings, severity badges, and compliant rewrites.
- **Citation Verification**: Cross-references AI citations with active database records to flag and prevent hallucinated policy references.
- **Human Approval Workflow**: Field-by-field review with side-by-side visual comparisons (Original vs AI Suggestion vs Final), allowing reviewers to Approve, Edit, or Reject revisions.
- **Batch Processing & CSV Import**: Import product catalogs via CSV with row-by-row validation, and execute sequential batch AI reviews with per-item failure isolation.
- **Editable Policy Library**: Search, filter, add, edit, and toggle active status of marketplace compliance rules.
- **Audit & Review History**: Complete audit trail tracking who reviewed, approved, edited, or rejected each listing revision with exact timestamps.

---

## 3. Technology Stack

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router DOM v6
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Testing**: Vitest & React Testing Library with JSDOM

### Backend
- **Language**: Python 3.11+
- **Framework**: Flask
- **ORM & Database**: Flask-SQLAlchemy, PyMySQL (MySQL 8.0+ supported, with automatic SQLite fallback for local developer agility)
- **WSGI Production Server**: Gunicorn
- **Environment**: python-dotenv, cryptography
- **Testing**: Pytest

### AI Integration
- **SDK**: Official Groq Python SDK (`groq`)
- **Default Model**: `openai/gpt-oss-20b` (configurable through `GROQ_MODEL`)
- **Mode**: Structured Outputs with JSON Schema (`response_format={"type": "json_schema"}`) with graceful fallback to JSON Mode (`response_format={"type": "json_object"}`)
- **Security**: Strictly backend-only; API keys are never exposed to the frontend client.

---

## 4. Architecture & Workflow

```
[ Seller / Reviewer ]
        │
        ▼
[ React + Tailwind Frontend (Vite) ]
        │  REST APIs (Axios)
        ▼
[ Flask Application Factory ]
   ├── Step 1: Deterministic Validation Engine (Python regex, duplicate check)
   ├── Step 2: Policy Retrieval Service (Keyword & Category MySQL query)
   ├── Step 3: Groq AI Engine (`groq` SDK + JSON Schema enforcement)
   ├── Step 4: Policy Citation Verifier (Checks policy_id in DB)
   └── Step 5: Database Transactions (db.session: Reviews, Findings, Suggestions)
        │
        ▼
[ MySQL 8.0 / SQLite Fallback Database ]
        │
        ▼
[ Human Approval Workflow ]
   ├── Approve ──> Updates Listing field in MySQL + Logs ReviewAction & AuditLog
   ├── Edit ─────> Modifies suggestion text + Applies to Listing + Logs Action
   └── Reject ───> Retains original content + Records reason in AuditLog
```

---

## 5. Folder Structure

```
marketplace-listing-quality-reviewer/
├── backend/
│   ├── app/
│   │   ├── models/            # SQLAlchemy database models
│   │   │   ├── action.py      # ReviewAction (audit trail of human decisions)
│   │   │   ├── audit.py       # AuditLog (system & user audit records)
│   │   │   ├── listing.py     # Listing entity
│   │   │   ├── policy.py      # Policy knowledge base entity
│   │   │   ├── review.py      # Review & ReviewFinding entities
│   │   │   ├── suggestion.py  # Suggestion entity for human workflow
│   │   │   ├── user.py        # User entity
│   │   │   └── __init__.py
│   │   ├── routes/            # REST API Blueprints
│   │   │   ├── batch.py       # Batch review and CSV import
│   │   │   ├── dashboard.py   # Dashboard metrics and distributions
│   │   │   ├── health.py      # System health and diagnostics
│   │   │   ├── history.py     # Global & listing audit logs
│   │   │   ├── listings.py    # Listing CRUD & deterministic validation
│   │   │   ├── policies.py    # Policy knowledge base management
│   │   │   ├── reviews.py     # AI review trigger & report fetch
│   │   │   ├── suggestions.py # Human approval, edit & reject actions
│   │   │   └── __init__.py
│   │   ├── services/          # Business logic & integrations
│   │   │   ├── audit_service.py       # Persistent audit logger
│   │   │   ├── groq_service.py        # Groq SDK integration & JSON schema enforcement
│   │   │   ├── policy_service.py      # Policy retrieval & citation verifier
│   │   │   └── validation_service.py  # Deterministic validation engine
│   │   ├── tests/             # Pytest test suite (32 tests)
│   │   ├── utils/             # Data seeders & response helpers
│   │   ├── config.py          # App configuration
│   │   ├── database.py        # Database setup & resilience
│   │   └── __init__.py        # Flask app factory
│   ├── requirements.txt
│   ├── run.py                 # Development runner
│   ├── .env.example
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── api/client.js      # Axios instance with interceptors
│   │   ├── components/        # Reusable UI components
│   │   ├── context/           # Toast notification provider
│   │   ├── pages/             # 9 Application views
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Listings.jsx
│   │   │   ├── ListingForm.jsx
│   │   │   ├── ListingDetail.jsx
│   │   │   ├── AIReviews.jsx
│   │   │   ├── ReviewReport.jsx
│   │   │   ├── PolicyLibrary.jsx
│   │   │   ├── ReviewHistory.jsx
│   │   │   └── Settings.jsx
│   │   ├── __tests__/         # Vitest frontend test suite
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vercel.json
│   └── .env.example
├── policy_documents/
│   └── sample_policies.json   # 14 demonstration policies
├── render.yaml                # Render production deployment configuration
├── README.md
├── AGENT_USAGE.md
└── .gitignore
```

---

## 6. Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: v18 or higher (v20+ recommended)
- **MySQL**: MySQL Server 8.0+ (optional for local dev: SQLite works out-of-the-box)
- **Groq API Key**: From [Groq Console](https://console.groq.com/keys)

---

## 7. Installation & Local Setup

### Step 1: Clone the Repository
```bash
git clone <repository_url>
cd "AI-powered Marketplace Listing Quality Reviewer"
```

### Step 2: Backend Setup
1. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Install Python dependencies:
   ```powershell
   pip install -r backend/requirements.txt
   ```
3. Configure environment variables:
   Copy `backend/.env.example` to `backend/.env` and provide your credentials:
   ```env
   SECRET_KEY=your-secure-random-secret
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_DATABASE=marketplace_reviewer
   AI_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=openai/gpt-oss-20b
   ```
   *(Note: If local MySQL is not running or credentials are not supplied, the backend automatically falls back to local SQLite without crashing).*

4. Run the backend server:
   ```powershell
   cd backend
   python run.py
   ```
   The backend API runs on `http://127.0.0.1:5000`.

### Step 3: Frontend Setup
1. Open a new terminal in the `frontend` directory:
   ```powershell
   cd frontend
   npm install
   ```
2. Run the frontend development server:
   ```powershell
   npm run dev
   ```
   The React application runs on `http://localhost:5173`.

---

## 8. Database Initialization & Seeding

The database initializes automatically when the backend boots:
1. Verifies connectivity to MySQL or switches to SQLite.
2. Creates all tables (`users`, `listings`, `policies`, `reviews`, `review_findings`, `suggestions`, `review_actions`, `audit_logs`).
3. Seeds the default Compliance Officer user (`compliance@marketplace.local`).
4. Seeds 14 demonstration policies covering titles, descriptions, medical claims, off-platform redirects, promotional superlatives, pricing transparency, and trademarks.
5. Seeds realistic sample listings (including non-compliant herbal tea, compliant headphones, and counterfeit electronics).

---

## 9. Running Tests

### Backend Tests (Pytest)
Run the 32 backend unit and integration tests (including validation, duplicate detection, policy verification, review workflow, Groq integration, and batch processing):
```powershell
cd backend
python -m pytest -v
```
*All tests use isolated mock AI responses and in-memory SQLite, requiring zero external API credits.*

### Frontend Tests (Vitest)
Run the 13 frontend component and workflow tests:
```powershell
cd frontend
npm test
```

### Frontend Production Build Verification
Verify that the production asset bundle builds cleanly:
```powershell
cd frontend
npm run build
```

---

## 10. API Endpoint Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/stats` | Retrieves real database summary metrics and severity distributions |
| `GET` | `/api/listings` | Lists listings with search, category/status filters, sorting, and pagination |
| `POST` | `/api/listings` | Creates listing with deterministic validation |
| `GET` | `/api/listings/<id>` | Retrieves single listing with review history |
| `PUT` | `/api/listings/<id>` | Updates listing after validation |
| `DELETE` | `/api/listings/<id>` | Deletes listing and logs audit entry |
| `POST` | `/api/listings/<id>/validate` | Runs deterministic pre-validation only |
| `POST` | `/api/listings/<id>/review` | Retrieves policies, calls Groq AI, verifies citations, stores findings |
| `GET` | `/api/reviews/<id>` | Retrieves review report details and suggestions |
| `POST` | `/api/suggestions/<id>/approve` | Approves revision, applies text to listing field, records action |
| `PUT` | `/api/suggestions/<id>` | Edits suggested revision wording |
| `POST` | `/api/suggestions/<id>/reject` | Rejects revision, preserves original content, logs reason |
| `GET` | `/api/policies` | Lists policies with category/status filtering |
| `POST` | `/api/policies` | Creates a new policy rule |
| `PUT` | `/api/policies/<id>` | Updates policy or toggles active status |
| `DELETE` | `/api/policies/<id>` | Deletes policy |
| `POST` | `/api/batch/review` | Sequentially processes a batch of listing IDs with error isolation |
| `POST` | `/api/batch/import-csv` | Parses CSV file/text, validates rows, and imports listings |
| `GET` | `/api/history` | Global audit logs |
| `GET` | `/api/listings/<id>/history` | Listing-specific audit trail & revision decisions |
| `GET` | `/api/health` | Service health, database type, and Groq config status |

---

## 11. Sample Inputs for Testing Workflows

### Sample Non-Compliant Listing (High Violations)
```json
{
  "title": "MIRACLE HERBAL TEA 100% CURES DIABETES & CANCER FAST WEIGHT LOSS GUARANTEED",
  "description": "Our miraculous natural herbal detox tea is scientifically proven to completely cure chronic diabetes, arthritis, and cancer in 14 days! You will lose 15kg in one week with zero dieting. Order directly on WhatsApp at +1-555-0199 for 20% discount off-platform! Visit our secret shop at https://miracle-cures.fake/buy.",
  "category": "Health & Personal Care",
  "price": 49.99,
  "currency": "USD",
  "listing_type": "Product",
  "seller": "Vitality Miracle Labs",
  "attributes": {
    "Volume": "250g",
    "Form": "Loose Leaf"
  },
  "tags": ["miracle", "weight loss", "cure diabetes", "cancer", "detox"]
}
```

### Sample Compliant Listing
```json
{
  "title": "UltraBass Pro Wireless Noise Cancelling Over-Ear Headphones Bluetooth 5.3",
  "description": "Experience pristine acoustics with the UltraBass Pro wireless headphones. Features active noise cancellation up to 35dB, 40mm neodymium dynamic audio drivers, ergonomic protein leather memory foam ear cushions, and up to 40 hours continuous playtime on a single charge. Includes USB-C fast charging cable, 3.5mm auxiliary cable, and protective travel case.",
  "category": "Electronics & Gadgets",
  "price": 129.50,
  "currency": "USD",
  "listing_type": "Product",
  "seller": "SonicTech Audio Direct",
  "attributes": {
    "Battery Life": "40 Hours",
    "Connectivity": "Bluetooth 5.3",
    "Noise Cancellation": "Active (ANC 35dB)",
    "Color": "Matte Black"
  },
  "tags": ["headphones", "bluetooth", "noise cancelling", "wireless audio"]
}
```

---

## 12. Deployment Instructions

### Deploying Frontend to Vercel
1. Push repository to GitHub.
2. In Vercel, select **Add New Project** and choose the repository.
3. Set **Root Directory** to `frontend`.
4. Framework Preset: **Vite**.
5. Set Environment Variable:
   - `VITE_API_URL`: `https://your-backend-app.onrender.com`
6. Click **Deploy**. Single-page app routing is handled by `frontend/vercel.json`.

### Deploying Backend to Render
1. In Render, select **New Web Service** and link the repository.
2. Root Directory: `backend`.
3. Runtime: **Python 3**.
4. Build Command: `pip install -r requirements.txt`.
5. Start Command: `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT`.
6. Add Environment Variables:
   - `SECRET_KEY`: `<generate random secret>`
   - `SQLALCHEMY_DATABASE_URI`: `mysql+pymysql://<user>:<password>@<hosted-mysql-host>:3306/<database>`
   - `AI_PROVIDER`: `groq`
   - `GROQ_API_KEY`: `<your Groq API key>`
   - `GROQ_MODEL`: `openai/gpt-oss-20b`
   - `CORS_ORIGINS`: `https://your-frontend-app.vercel.app`
7. Click **Deploy Web Service**.

---

## 13. Limitations & Excluded Scope

- **Image Analysis**: Current scope focuses on text attributes, specifications, and claim content. Product image OCR and computer vision inspection are out of scope.
- **Multilingual Tokenization**: Demonstration policies and keyword indexing are optimized for English.
- **Microservices / Kubernetes**: Explicitly excluded per project design guidelines in favor of a lean, reliable modular monolith.
