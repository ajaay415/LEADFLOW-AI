"""FastAPI application for the LEADFLOW AI lead pipeline."""

import os
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from ai_service import analyze_lead_with_ai, generate_customer_response
from email_service import send_lead_email


app = FastAPI(
    title="LEADFLOW AI",
    description="AI-powered lead capture, qualification, and follow-up API.",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = os.getenv(
    "DATABASE_PATH",
    str(Path(__file__).with_name("leadflow.db")),
)


def get_connection():
    connection = sqlite3.connect(DATABASE, timeout=15)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_connection()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                company TEXT,
                requirement TEXT NOT NULL,
                budget REAL,
                lead_score INTEGER,
                category TEXT,
                priority TEXT,
                recommended_action TEXT,
                status TEXT NOT NULL DEFAULT 'NEW',
                email_approved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Lightweight migration for databases created by earlier versions.
        existing = {
            row["name"] for row in connection.execute("PRAGMA table_info(leads)").fetchall()
        }
        migrations = {
            "status": "ALTER TABLE leads ADD COLUMN status TEXT NOT NULL DEFAULT 'NEW'",
            "email_approved": "ALTER TABLE leads ADD COLUMN email_approved INTEGER NOT NULL DEFAULT 0",
            "created_at": "ALTER TABLE leads ADD COLUMN created_at TEXT",
            "updated_at": "ALTER TABLE leads ADD COLUMN updated_at TEXT",
        }
        for column, statement in migrations.items():
            if column not in existing:
                connection.execute(statement)
        connection.execute(
            "UPDATE leads SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP), "
            "updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)"
        )
        connection.commit()
    finally:
        connection.close()


create_database()


class Lead(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    company: Optional[str] = Field(default=None, max_length=160)
    requirement: str = Field(min_length=5, max_length=5000)
    budget: Optional[float] = Field(default=None, ge=0)


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    company: Optional[str] = Field(default=None, max_length=160)
    requirement: Optional[str] = Field(default=None, min_length=5, max_length=5000)
    budget: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = None


@app.get("/")
def home():
    return {"message": "LEADFLOW AI API is running", "status": "success"}


@app.get("/health")
def health():
    connection = get_connection()
    try:
        connection.execute("SELECT 1")
    except sqlite3.Error as error:
        raise HTTPException(status_code=503, detail="Database unavailable") from error
    finally:
        connection.close()

    return {
        "status": "healthy",
        "service": "LEADFLOW AI",
        "database": "connected",
        "ai_model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        "ai_mode": "ollama-with-offline-fallback",
    }


@app.post("/leads", status_code=201)
def create_lead(lead: Lead):
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO leads (name, email, company, requirement, budget)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                lead.name.strip(),
                str(lead.email),
                lead.company.strip() if lead.company else None,
                lead.requirement.strip(),
                lead.budget,
            ),
        )
        lead_id = cursor.lastrowid
        connection.commit()
    except sqlite3.Error as error:
        connection.rollback()
        raise HTTPException(status_code=500, detail="Lead could not be saved") from error
    finally:
        connection.close()

    analysis_result = analyze_lead(lead_id)

    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Created lead could not be retrieved")

    return {
        "message": "Lead created and analyzed successfully",
        "lead": dict(row),
        "analysis": analysis_result["analysis"],
    }





@app.get("/dashboard/stats")
def dashboard_stats():
    connection = get_connection()
    try:
        total = connection.execute("SELECT COUNT(*) AS n FROM leads").fetchone()["n"]
        rows = connection.execute(
            "SELECT status, COUNT(*) AS count FROM leads GROUP BY status"
        ).fetchall()
        priorities = connection.execute(
            "SELECT priority, COUNT(*) AS count FROM leads GROUP BY priority"
        ).fetchall()
        aggregates = connection.execute(
            "SELECT COALESCE(SUM(budget), 0) AS pipeline_value, "
            "COALESCE(AVG(lead_score), 0) AS average_score FROM leads"
        ).fetchone()
        recent = connection.execute(
            "SELECT * FROM leads ORDER BY created_at DESC, id DESC LIMIT 5"
        ).fetchall()
        return {
            "total_leads": total,
            "by_status": {row["status"]: row["count"] for row in rows},
            "by_priority": {row["priority"] or "UNSCORED": row["count"] for row in priorities},
            "pipeline_value": aggregates["pipeline_value"],
            "average_score": round(aggregates["average_score"], 1),
            "recent_leads": [dict(row) for row in recent],
        }
    finally:
        connection.close()


@app.put("/leads/{lead_id}")
def update_lead(lead_id: int, updates: LeadUpdate):
    values = updates.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=400, detail="No lead fields supplied")
    if "status" in values:
        allowed_statuses = {"NEW", "CONTACTED", "QUALIFIED", "PROPOSAL", "WON", "LOST"}
        values["status"] = str(values["status"]).upper()
        if values["status"] not in allowed_statuses:
            raise HTTPException(status_code=422, detail="Invalid lead status")
    if "email" in values and values["email"] is not None:
        values["email"] = str(values["email"])
    if "name" in values and values["name"] is not None:
        values["name"] = values["name"].strip()
    if "requirement" in values and values["requirement"] is not None:
        values["requirement"] = values["requirement"].strip()
    values["updated_at"] = "CURRENT_TIMESTAMP"

    assignments = ", ".join(
        f"{column} = ?" if value != "CURRENT_TIMESTAMP" else f"{column} = CURRENT_TIMESTAMP"
        for column, value in values.items()
    )
    params = [value for value in values.values() if value != "CURRENT_TIMESTAMP"]
    params.append(lead_id)

    connection = get_connection()
    try:
        cursor = connection.execute(
            f"UPDATE leads SET {assignments} WHERE id = ?", params
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        connection.commit()
        row = connection.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row)
    finally:
        connection.close()


@app.delete("/leads/{lead_id}")
def delete_lead(lead_id: int):
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        connection.commit()
        return {"message": "Lead deleted", "lead_id": lead_id}
    finally:
        connection.close()


@app.get("/leads")
def get_all_leads():
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM leads ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


@app.get("/leads/{lead_id}")
def get_lead(lead_id: int):
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return dict(row)


@app.post("/leads/{lead_id}/analyze")
def analyze_lead(lead_id: int):
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead = dict(row)
    ai_result = analyze_lead_with_ai(
        name=lead["name"],
        company=lead["company"],
        requirement=lead["requirement"],
        budget=lead["budget"],
    )

    parsed = {
        "lead_score": 40,
        "category": "General Enquiry",
        "priority": "MEDIUM",
        "intent": "General customer enquiry",
        "recommended_action": "Follow up with customer",
    }
    labels = {
        "LEAD_SCORE": "lead_score",
        "CATEGORY": "category",
        "PRIORITY": "priority",
        "INTENT": "intent",
        "RECOMMENDED_ACTION": "recommended_action",
    }

    for line in ai_result.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in labels and value.strip():
            parsed[labels[key.strip()]] = value.strip()

    try:
        parsed["lead_score"] = max(0, min(int(parsed["lead_score"]), 100))
    except (TypeError, ValueError):
        parsed["lead_score"] = 40

    parsed["priority"] = str(parsed["priority"]).upper()
    if parsed["priority"] not in {"HIGH", "MEDIUM", "LOW"}:
        parsed["priority"] = "MEDIUM"

    connection = get_connection()
    try:
        connection.execute(
            """
            UPDATE leads
            SET lead_score = ?, category = ?, priority = ?, recommended_action = ?
            WHERE id = ?
            """,
            (
                parsed["lead_score"],
                parsed["category"],
                parsed["priority"],
                parsed["recommended_action"],
                lead_id,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    return {
        "message": "Lead analyzed successfully",
        "analysis": {
            "lead_id": lead_id,
            "customer": lead["name"],
            **parsed,
        },
        "raw_ai_response": ai_result,
    }


@app.get("/leads/{lead_id}/response")
def generate_response(lead_id: int):
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead = dict(row)
    response = generate_customer_response(
        name=lead["name"],
        company=lead["company"],
        requirement=lead["requirement"],
        budget=lead["budget"],
        priority=lead["priority"],
        category=lead["category"],
    )
    return {
        "lead_id": lead_id,
        "customer": lead["name"],
        "suggested_response": response,
    }


@app.post("/leads/{lead_id}/approve")
def approve_lead_response(lead_id: int):
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT id FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Lead not found")
        connection.execute(
            "UPDATE leads SET email_approved = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (lead_id,),
        )
        connection.commit()
    finally:
        connection.close()

    return {
        "message": "Follow-up approved",
        "lead_id": lead_id,
        "status": "APPROVED",
        "next_action": "Ready to send to customer",
    }


@app.post("/leads/{lead_id}/send-email")
async def send_email_to_lead(lead_id: int):
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead = dict(row)
    if not lead.get("email_approved"):
        raise HTTPException(
            status_code=403,
            detail="Approve this follow-up before sending the email.",
        )
    message = generate_customer_response(
        name=lead["name"],
        company=lead["company"],
        requirement=lead["requirement"],
        budget=lead["budget"],
        priority=lead["priority"],
        category=lead["category"],
    )

    try:
        await send_lead_email(
            customer_email=lead["email"],
            customer_name=lead["name"],
            message=message,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="Email delivery failed") from error

    return {
        "message": "Email sent successfully",
        "lead_id": lead_id,
        "customer": lead["name"],
        "email": lead["email"],
        "status": "SENT",
    }
