# Excel/LibreOffice Template Mapper MVP (Web + Audit Trail + PDF Export)

This is a minimal MVP for the workflow you described:

1) Admin uploads a spreadsheet template (.xlsx or .ods)  
2) Admin maps editable cells (e.g., A1, B7...)  
3) Operator opens a template instance and can edit **only mapped cells**  
4) The UI shows the sheet; other cells are read-only; formulas are preserved  
5) System records an audit trail (who/when/what changed)  
6) Export generates a PDF of the spreadsheet + a final page with the audit log.

## What this MVP does (and what it doesn't)

### ✅ Included
- Web app: React (Vite) frontend + FastAPI backend
- Postgres database (Railway)
- Upload template (.xlsx or .ods)
- Map editable cells
- Fill mapped cells + store values
- Audit trail per save/edit
- Export PDF:
  - fills values into a copy of the template
  - recalculates using LibreOffice headless conversion
  - appends a last PDF page with audit trail

### ⚠️ Important limitations (MVP)
- In-browser formula recalculation is **best-effort** (Handsontable + HyperFormula can handle many common functions, but not 100% Excel parity).
- The **export** is the authoritative output: LibreOffice converts the filled spreadsheet to PDF (more consistent for formulas).
- File storage is in Postgres as `bytea` (works for MVP, but for production use S3/Blob storage).

## Tech stack
- Frontend: React + Vite + Handsontable + HyperFormula + SheetJS
- Backend: FastAPI + SQLAlchemy + Alembic + Postgres
- PDF: LibreOffice headless for conversion + ReportLab for audit page + pypdf merge

---

## Deploy on Railway (Docker)
This repo contains a backend `Dockerfile` that installs LibreOffice. Railway will:
- build the container
- run DB migrations automatically on startup
- start the API

### Railway environment variables
Set these in Railway:
- `DATABASE_URL` = provided by Railway Postgres
- `JWT_SECRET` = a long random string
- `CORS_ORIGINS` = e.g. `https://your-frontend-domain.com,http://localhost:5173`
- `ADMIN_EMAIL` = initial admin email
- `ADMIN_PASSWORD` = initial admin password

### Frontend hosting
Deploy the `frontend/` folder to GitHub Pages or any static host. Configure:
- `VITE_API_URL` in `frontend/.env` (or host env var) to the Railway backend URL.

---

## Local dev
### Backend
```bash
cd backend
cp .env.example .env
# set DATABASE_URL
docker compose up --build
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## API quick overview
- POST `/auth/login`
- GET `/me`
- POST `/templates` (admin upload)
- POST `/templates/{id}/map` (admin map cells)
- GET `/templates/{id}/workbook` (download)
- POST `/instances` (create filled sheet instance from template)
- GET `/instances/{id}`
- POST `/instances/{id}/save` (values + audit)
- POST `/instances/{id}/export` (PDF)

