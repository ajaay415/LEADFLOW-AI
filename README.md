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

## 4. Gmail SMTP setup (optional)

To enable follow-up email delivery, use a Google App Password. First enable 2-Step Verification on the Google Account, then create an App Password at https://myaccount.google.com/apppasswords (if the option is available for your account). App Passwords may be unavailable for some account types or security configurations.

Add these values to `backend/.env`:

```env
MAIL_USERNAME=your-gmail-address@gmail.com
MAIL_PASSWORD=your-16-character-app-password
MAIL_FROM=your-gmail-address@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
```

Use the 16-character App Password as `MAIL_PASSWORD`, not your regular Google password. Keep `backend/.env` private and never commit it. Sending also depends on the Gmail account's SMTP access and Google's current account limits. The application requires explicit approval before sending a follow-up.
