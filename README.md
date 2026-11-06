# LEADFLOW AI

AI-assisted lead capture, qualification, and customer follow-up. The frontend is built with React + Vite; the API uses FastAPI and SQLite; lead analysis uses a local Ollama model with an offline rules-based fallback.

## Features

- Capture customer name, email, company, requirement, and optional budget.
- Store leads in a local SQLite database.
- Score and categorize leads with Ollama (`llama3.2:3b` by default).
- Fall back to deterministic local scoring when Ollama is unavailable.
- List, retrieve, update, and delete leads through the REST API.
- View CRM KPIs, pipeline status, priority counts, and recent leads in the dashboard.
- Generate customer follow-up drafts.
- Send follow-up emails when SMTP credentials are configured.

## Requirements

- Windows 10/11, macOS, or Linux
- Python 3.10+
- Node.js 20.19+ or 22.12+
- Ollama (optional, recommended for AI analysis)

## 1. Start Ollama

Install Ollama, then pull the model:

```powershell
ollama pull llama3.2:3b
```

Make sure the Ollama service is running. On Windows, the Ollama desktop app normally runs it in the background. You can verify the model with:

```powershell
ollama list
```

If Ollama is not running, lead capture still works using the offline fallback scorer.

## 2. Run the backend

Open PowerShell in the repository:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API health check: http://127.0.0.1:8000/health

Interactive API documentation: http://127.0.0.1:8000/docs

The SQLite database is created automatically in the backend directory by default. Do not commit the generated database or your real `.env` file.

## 3. Run the frontend

Open a second PowerShell window in the repository:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173). The CRM dashboard is available at http://localhost:5173/dashboard.

## 4. Outlook email setup (optional)

To enable follow-up email delivery, edit `backend/.env` and set:

```env
MAIL_USERNAME=your-outlook-address@outlook.com
MAIL_PASSWORD=your-mail-provider-approved-credential
MAIL_FROM=your-outlook-address@outlook.com
MAIL_PORT=587
MAIL_SERVER=smtp.office365.com
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
```

For a personal Outlook.com mailbox, use `MAIL_SERVER=smtp-mail.outlook.com`. For Microsoft 365 work or school mailboxes, use `smtp.office365.com`. Both use port 587 with STARTTLS. The mailbox must allow SMTP AUTH; Microsoft 365 administrators may need to enable authenticated SMTP for the mailbox. Use an app password only if your account and organization support it, or configure an approved OAuth-based mail integration if password-based SMTP is disabled. Never commit `backend/.env` or share mailbox credentials. Email sending remains unavailable until valid credentials and provider-side SMTP access are configured.

## Main API routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/` | API status |
| GET | `/health` | Database/API health |
| POST | `/leads` | Create and analyze a lead |
| GET | `/leads` | List leads |
| GET | `/leads/{lead_id}` | Retrieve one lead |
| PUT | `/leads/{lead_id}` | Update lead details or pipeline status |
| DELETE | `/leads/{lead_id}` | Delete a lead |
| GET | `/dashboard/stats` | CRM dashboard metrics and recent leads |
| POST | `/leads/{lead_id}/analyze` | Re-run lead analysis |
| GET | `/leads/{lead_id}/response` | Generate a follow-up draft |
| POST | `/leads/{lead_id}/approve` | Explicitly approve a follow-up email |
| POST | `/leads/{lead_id}/send-email` | Send the follow-up email |

## Configuration

Frontend API URL is controlled by `VITE_API_URL`. Backend settings are in `backend/.env`:

- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT`
- `CORS_ORIGINS`
- Optional `MAIL_*` SMTP values

## Deployment note

This repository is configured for local development with Ollama on the same machine as the API. A public frontend cannot reach a visitor's `127.0.0.1` Ollama service. For public production deployment, host the API and model on an appropriately secured server, configure the production frontend origin in `CORS_ORIGINS`, and use persistent storage for the database. Never expose Ollama or SMTP credentials directly to the browser.
