# Euroshub Lead Management — Sales Hub

> **Internal CRM & Sales Pipeline Intelligence System** for Euroshub Software House

A production-grade full-stack application that helps Euroshub sales employees manage leads, track pipeline stages, log client touchpoints, generate AI-powered proposals, and monitor conversion performance — all from a unified dark-mode dashboard.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [Database Setup (Supabase + RLS)](#database-setup)
6. [Environment Variables](#environment-variables)
7. [AI Configuration (Gemini)](#ai-configuration)
8. [PDF Generation](#pdf-generation)
9. [Demo Accounts](#demo-accounts)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Features Reference](#features-reference)

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│             Browser (React/Vite)            │
│  Dashboard · Leads · Pipeline · Tasks · AI  │
└─────────────────┬───────────────────────────┘
                  │ HTTP (Axios)
┌─────────────────▼───────────────────────────┐
│        FastAPI Backend (Python 3.11+)        │
│  /auth  /leads  /activities  /tasks          │
│  /ai    /proposals  /dashboard  /reports     │
└─────────────────┬───────────────────────────┘
                  │ asyncpg / supabase-py
┌─────────────────▼───────────────────────────┐
│         Supabase (PostgreSQL + RLS)          │
│  leads · activities · tasks · proposals      │
│  profiles · status_history · settings        │
└─────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Google Gemini API                    │
│  Lead scoring · Proposal drafting            │
│  Sentiment analysis · Scope extraction       │
└─────────────────────────────────────────────┘
```

**Key Design Decisions:**
- **SPA with Hash-based routing** — No SSR needed; pure React frontend deployed to any static host
- **FastAPI backend** — All AI calls and PDF generation are server-side; API keys never reach the browser
- **Supabase RLS** — Row-level security enforced at the database level for admin vs employee roles
- **AI on-demand only** — Gemini is never auto-triggered; every AI operation requires an explicit user action
- **Fallback heuristics** — If Gemini API is unavailable, backend returns heuristic-based scores/proposals so the app remains functional

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite 8 + Tailwind CSS v4 |
| Icons | Lucide React |
| Charts | Recharts |
| HTTP Client | Axios |
| Backend | FastAPI + Uvicorn (Python 3.11+) |
| Database | PostgreSQL via Supabase |
| Auth | Supabase Auth (JWT) |
| AI Engine | Google Gemini 1.5 Pro (via google-generativeai) |
| PDF Export | ReportLab |
| Testing | Pytest + HTTPX |

---

## Project Structure

```
AI Lead Analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app + CORS + router registration
│   │   ├── config.py             # Settings (Pydantic BaseSettings)
│   │   ├── database.py           # Supabase async client
│   │   ├── models/               # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── auth.py           # Login, signup, user management
│   │   │   ├── leads.py          # Lead CRUD + duplicate detection
│   │   │   ├── activities.py     # Activity / touchpoint logging
│   │   │   ├── tasks.py          # Task management
│   │   │   ├── ai.py             # AI analysis endpoints
│   │   │   ├── proposals.py      # Proposal CRUD + PDF export
│   │   │   ├── dashboard.py      # KPI stats aggregation
│   │   │   ├── reports.py        # Conversion + source analytics
│   │   │   └── settings.py       # Profile + lead source config
│   │   └── services/
│   │       ├── gemini_client.py  # Gemini API wrapper
│   │       ├── prompts.py        # Structured prompts for all AI tasks
│   │       └── pdf_generator.py  # ReportLab proposal PDF builder
│   ├── tests/
│   │   └── test_api.py           # 8-test Pytest suite
│   ├── schema.sql                # Full PostgreSQL schema + RLS policies
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── auth/
│   │   │   └── AuthContext.jsx   # Auth state + demo user switching
│   │   ├── components/
│   │   │   ├── ai/               # AILeadAnalyzer, AIScoreCard, ConversationAnalyzerModal
│   │   │   ├── activities/       # ActivityTimeline, AddActivityModal
│   │   │   ├── common/           # Button, Badge, Modal, LoadingSpinner, EmptyState
│   │   │   ├── layout/           # MainLayout, Sidebar, Header
│   │   │   ├── leads/            # LeadFormModal, StatusBadge, PriorityBadge, FollowUpIndicator
│   │   │   ├── proposals/        # ProposalList, ProposalDraftModal
│   │   │   └── tasks/            # TaskModal
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx     # KPI cards, funnel, source chart, follow-up radar
│   │   │   ├── Leads.jsx         # Lead directory + multi-filter + CSV export
│   │   │   ├── LeadDetail.jsx    # 6-tab lead workspace
│   │   │   ├── Pipeline.jsx      # Kanban board
│   │   │   ├── Tasks.jsx         # Task center
│   │   │   ├── FollowUps.jsx     # Overdue / Today / Upcoming buckets
│   │   │   ├── Reports.jsx       # Conversion metrics + CSV export
│   │   │   ├── Users.jsx         # Admin: team & role management
│   │   │   ├── Settings.jsx      # Profile + lead source editor
│   │   │   ├── Login.jsx
│   │   │   └── SignUp.jsx
│   │   ├── services/
│   │   │   └── api.js            # Axios API client (all endpoints)
│   │   ├── utils/
│   │   │   ├── formatters.js     # Date, currency, initials helpers
│   │   │   └── constants.js      # Pipeline stages, priorities, activity types
│   │   └── App.jsx               # Root router + layout coordinator
│   ├── index.html
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── .env.example                  # Root-level env template
└── README.md
```

---

## Quick Start

### Prerequisites

- **Node.js** 20+
- **Python** 3.11+
- **Supabase account** (free tier is sufficient)
- **Google AI Studio API key** (for Gemini)

### 1. Clone and Install

```powershell
# Install Python dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# Install Node dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
```

Edit `backend/.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
GEMINI_API_KEY=your-gemini-api-key
SECRET_KEY=any-long-random-string-for-jwt
```

Edit `frontend/.env.local`:
```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Set Up Database

1. Go to your **Supabase Dashboard > SQL Editor**
2. Copy the contents of `backend/schema.sql`
3. Paste and run — this creates all tables, indexes, triggers, and RLS policies

### 4. Run Dev Servers

**Terminal 1 — Backend:**
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000 --app-dir backend
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Database Setup

### Schema Overview

| Table | Purpose |
|-------|---------|
| `profiles` | Extended user data (name, role: admin/employee) |
| `leads` | Core lead records with all CRM fields |
| `activities` | Touchpoint log (calls, emails, WhatsApp, meetings, notes) |
| `tasks` | Internal action items linked to leads |
| `proposals` | Commercial proposals with pricing and PDF tracking |
| `status_history` | Immutable audit trail of pipeline stage transitions |
| `lead_sources` | Configurable inbound source list |
| `ai_analyses` | Persisted Gemini analysis results |

### Row-Level Security (RLS)

- **Admins** — Full read/write on all leads, activities, tasks, and proposals
- **Employees** — Can only read/write leads they created or are assigned to

The `handle_new_user` trigger automatically creates a `profiles` record on signup with the default role `employee`.

### Manual Promotion to Admin

```sql
UPDATE profiles SET role = 'admin' WHERE email = 'your@email.com';
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Service role key (bypasses RLS for backend) |
| `GEMINI_API_KEY` | Yes | Google AI Studio API key |
| `SECRET_KEY` | Yes | JWT signing secret (32+ chars) |
| `ALGORITHM` | No | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token lifetime (default: 1440 = 24h) |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | FastAPI backend URL |
| `VITE_SUPABASE_URL` | Yes | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Yes | Supabase anon/public key |

---

## AI Configuration

All AI features use **Google Gemini 1.5 Pro** and are **strictly on-demand**.

### Available AI Operations

| Feature | Endpoint | Description |
|---------|---------|-------------|
| Lead Scoring | `POST /api/ai/score/{lead_id}` | Scores lead 0-100 across 4 dimensions |
| Scope Extraction | `POST /api/ai/extract-scope/{lead_id}` | Parses project requirements from description |
| Conversation Analysis | `POST /api/ai/analyze-conversation/{lead_id}` | Sentiment + intent from pasted transcript |
| Proposal Draft | `POST /api/proposals/{lead_id}/draft` | AI-written proposal with scope/timeline/pricing |

### Fallback Mode

If `GEMINI_API_KEY` is not set or the API is unavailable, the backend returns **heuristic-based results** so the app remains functional for demo/testing purposes.

---

## PDF Generation

```
GET /api/proposals/{proposal_id}/pdf
```

Generates a branded PDF with:
- Euroshub letterhead with gradient header
- Client and project details
- Executive Summary, Scope of Work, Deliverables
- Timeline and commercial terms
- Page numbers and footer

Built with **ReportLab**. Generated on-demand, no files stored on disk.

---

## Demo Accounts

The app includes a **demo mode** for evaluation. Switch roles using the header toggle:

| Role | Name | Email |
|------|------|-------|
| Admin | Alex Rivers | alex.rivers@euroshub.com |
| Employee | Sarah Chen | sarah.chen@euroshub.com |

**Admin** sees all leads and can manage team roles.
**Employee** sees only assigned leads and own activities/tasks.

---

## Testing

### Backend Tests (Pytest)

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
pytest tests/test_api.py -v
```

8 tests covering: health check, auth, lead CRUD, dashboard stats, AI scoring, reports, and activity retrieval. All pass.

### Frontend Build Validation

```powershell
cd frontend
npm run build
```

Result: 2526 modules transformed, 0 errors.

---

## Deployment

### Backend (Render / Railway / Fly.io)

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend
```

### Frontend (Vercel / Netlify / Cloudflare Pages)

- Build command: `cd frontend && npm run build`
- Output directory: `frontend/dist`
- Set `VITE_API_URL` to your deployed backend URL

### CORS

Update `backend/app/main.py` to restrict origins in production:
```python
allow_origins=["https://your-frontend-domain.com"]
```

---

## Features Reference

### Dashboard
KPI cards, conversion funnel, source distribution chart, overdue follow-ups, recent activity feed

### Lead Management
Full-text search, multi-filter (status/priority/source/assignee), sortable table, CSV export, duplicate detection

### Lead Detail (6 tabs)
1. **Overview** — All lead fields with inline editing
2. **AI Engine** — Lead scoring, scope extraction, conversation analysis
3. **Activity Timeline** — Chronological touchpoint log with follow-up scheduling
4. **Proposals** — AI-drafted proposals with PDF export
5. **Tasks** — Lead-scoped action items
6. **Status Journey** — Pipeline transition audit trail

### Pipeline (Kanban)
Visual board: NEW > CONTACTED > QUALIFIED > PROPOSAL_SENT > NEGOTIATION > WON/LOST.
Quick status updates from cards, budget totals per column.

### Tasks
Create, complete, delete tasks linked to leads. Filter by status and due date.

### Follow-Ups
Three-bucket view: Overdue, Due Today, Upcoming. Click to navigate to lead.

### Reports
Channel conversion table, stage funnel metrics, source revenue breakdown, CSV export.

### Team and Roles (Admin)
View employees, promote/demote between admin and employee roles.

### Settings
Update display name, configure custom lead sources.
