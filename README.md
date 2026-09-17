# O-Negative — AI-Driven Blood Coordination System

A production-grade, healthcare-specialized AI agent system for coordinating urgent blood requests and clinical donor eligibility across India's blood banking infrastructure. Powered by **Google Gemini 3.6 Flash**, **Vector RAG (NBTC/NACO/WHO guidelines)**, **Persistent Memory (Supabase / SQLite)**, and **Interactive Next.js Dashboard**.

---

## 🏗️ System Architecture

```
                                    ┌──────────────────────────────────────────────────────────┐
                                    │                     Next.js Frontend                     │
                                    │               (Emergency Dashboard & Chat)               │
                                    └────────────────────────────┬─────────────────────────────┘
                                                                 │ REST / JSON (port 3000 -> 8000)
                                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                            FastAPI Backend (backend/main.py)                                 │
│                                                                                                              │
│  ┌───────────────────────┐   ┌────────────────────────┐   ┌──────────────────────┐   ┌─────────────────────┐ │
│  │   Agent Orchestrator  │   │      Knowledge RAG     │   │   Live Data Layer    │   │   Memory Database   │ │
│  │   (Google Gemini)     │   │   (ChromaDB + NBTC)    │   │  (data.gov.in / DB)  │   │ (Supabase / SQLite) │ │
│  └───────────┬───────────┘   └───────────┬────────────┘   └──────────┬───────────┘   └──────────┬──────────┘ │
│              │                           │                           │                          │            │
│              └───────────────────────────┴─────────────┬─────────────┴──────────────────────────┘            │
│                                                        ▼                                                     │
│                                       ┌──────────────────────────────────┐                                   │
│                                       │   Sandbox Alert Notification     │                                   │
│                                       │   (Twilio / Audit Trail)         │                                   │
│                                       └──────────────────────────────────┘                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Layers

1. **Agent Orchestrator (`backend/agent/`)**:
   - Google Gemini 3.6 Flash reasoning agent with temperature tuning and clinical prompt engineering
   - Transparent step-by-step reasoning trail and confidence scoring (0.0 to 1.0)
   - Deterministic clinical fallback for zero-downtime offline operation

2. **Knowledge Layer (`backend/knowledge/`)**:
   - Vector-indexed RAG using ChromaDB
   - 34 comprehensive clinical eligibility rules sourced directly from National Blood Transfusion Council (NBTC), NACO, and WHO guidelines
   - Covers deferral intervals, antibiotics/medications, infectious disease risk, and cross-match rules

3. **Live Data Layer (`backend/data_layer/`)**:
   - Government Blood Bank directory integration with data.gov.in API
   - Distance matrix calculations with Google Maps API and geodetic fallback
   - Live donor availability registry with geographic proximity matching

4. **Persistent Memory Layer (`backend/memory/`)**:
   - Dual-backend database engine supporting **Supabase PostgreSQL** and zero-config local **SQLite**
   - Tracks donor reliability scoring (response latency, successful donations)
   - Immutable audit logging for every clinical query and dispatched alert

5. **Notification Dispatcher (`backend/notifications/`)**:
   - Clinical alert dispatcher with sandbox simulation mode (safe, zero cost)
   - Twilio integration for live emergency SMS dispatch
   - SHA-256 cryptographic phone hashing for complete donor privacy

6. **Frontend Dashboard (`frontend/`)**:
   - Modern Next.js 14 application with Tailwind CSS
   - Real-time clinical reasoning accordion, live system health monitors, quick emergency templates, and notification audit viewer

---

## 📁 Clean Repository Structure

```
Rakt_Setu/
├── .env                     # Local environment credentials (git-ignored)
├── .env.example             # Template with all configurable variables
├── requirements.txt         # Consolidated Python dependencies
├── Procfile                 # Cloud deployment process definition (Render/Railway)
├── render.yaml              # Render infrastructure-as-code deployment blueprint
│
├── backend/                 # Python FastAPI Backend Architecture
│   ├── main.py              # Application entry point & CORS configuration
│   ├── config.py            # Centralized credential loading & validation
│   ├── agent/               # Clinical agent reasoning & orchestrator
│   │   └── orchestrator.py
│   ├── knowledge/           # RAG retrieval & NBTC clinical rule vector index
│   │   ├── rag_engine.py
│   │   └── eligibility_rules.py
│   ├── data_layer/          # Blood bank APIs & donor registry
│   │   ├── blood_banks.py
│   │   ├── donor_registry.py
│   │   └── seed_data.py
│   ├── memory/              # PostgreSQL (Supabase) + SQLite memory engine
│   │   ├── memory_db.py
│   │   └── schema.py
│   ├── notifications/       # Sandbox dispatcher & audit logger
│   │   └── notification_service.py
│   ├── api/                 # Modular FastAPI route controllers
│   │   ├── routes_system.py
│   │   ├── routes_query.py
│   │   ├── routes_donors.py
│   │   ├── routes_banks.py
│   │   └── routes_notifications.py
│   └── tests/               # End-to-end automated test suites
│       ├── test_data_layer.py
│       ├── test_memory.py
│       └── test_notifications.py
│
├── frontend/                # Next.js 14 React Dashboard
│   ├── app/                 # App Router (page.tsx, layout.tsx, globals.css)
│   ├── components/          # UI components (ChatInterface.tsx)
│   ├── package.json         # Node.js dependencies
│   ├── tailwind.config.js   # Tailwind theme setup
│   └── tsconfig.json        # TypeScript configuration
│
└── data/                    # Generated Runtime Data
    ├── donor_availability.db
    ├── rakt_setu_memory.db
    └── .chroma_data/
```

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Configure Environment
Create `.env` in the project root:
```bash
cp .env.example .env
```
Fill in your credentials:
```ini
GEMINI_API_KEY="your-gemini-api-key"
DATA_GOV_IN_API_KEY="your-data-gov-in-key"
GOOGLE_MAPS_API_KEY="your-google-maps-key"
DATABASE_URL="postgresql://postgres:password@host:5432/postgres"
NOTIFICATION_MODE="sandbox"
PORT=8000
```

### 3. Backend Setup & Startup
```bash
# Create virtual environment & install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run automated backend test suites
python backend/tests/test_data_layer.py
python backend/tests/test_memory.py
python backend/tests/test_notifications.py

# Start FastAPI backend server
python -m backend.main
# Server running at: http://localhost:8000
# OpenAPI Docs: http://localhost:8000/docs
```

### 4. Frontend Setup & Startup
Open a new terminal:
```bash
cd frontend
npm install
npm run dev
# Dashboard running at: http://localhost:3000
```

---

## 🧪 API Verification & Health Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Basic system health check |
| `/api/system/status` | GET | Active LLM, RAG rule count, memory DB status |
| `/api/query` | POST | Submits blood request or eligibility question to Gemini |
| `/api/banks` | GET | Nearby blood banks with distance calculation |
| `/api/donors` | GET | Registered donors filtered by location and blood group |
| `/api/notifications/dispatch` | POST | Dispatches emergency notification (sandbox or live) |
| `/api/notifications/audit` | GET | Returns full dispatch audit log |

---

## 🛡️ Clinical Integrity & Privacy

- **Data Privacy**: No Plaintext PII is exposed. Phone numbers are hashed using SHA-256.
- **Explainability**: Every clinical response provides the exact NBTC rule citation, reasoning steps, and model confidence score.
- **Zero Hallucination Guardrails**: Prompts are constrained to authoritative medical sources, falling back to conservative deferral when uncertain.
