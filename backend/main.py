
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
from fastapi import FastAPI, HTTPException


from ai_service import (
    analyze_lead_with_ai,
    generate_customer_response
)

from email_service import send_lead_email
app = FastAPI(
    title="LEADFLOW AI",
    
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# DATABASE
# ==========================================

DATABASE = "leadflow.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():

    connection = get_connection()

    connection.execute("""
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
            recommended_action TEXT
        )
    """)

    connection.commit()
    connection.close()


create_database()


# ==========================================
# DATA MODEL
# ==========================================

class Lead(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    requirement: str
    budget: Optional[float] = None


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "LEADFLOW AI API is running 🚀",
        "status": "success"
    }


# ==========================================
# HEALTH
# ==========================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "LEADFLOW AI",
        "database": "connected"
    }


# ==========================================
# CREATE LEAD
# ==========================================

@app.post("/leads")
def create_lead(lead: Lead):

    connection = get_connection()

    try:
        # 1. Save the new lead
        cursor = connection.execute(
            """
            INSERT INTO leads
            (name, email, company, requirement, budget)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                lead.name,
                lead.email,
                lead.company,
                lead.requirement,
                lead.budget
            )
        )

        lead_id = cursor.lastrowid

        connection.commit()

    except Exception as error:
        connection.rollback()
        connection.close()

        raise HTTPException(
            status_code=500,
            detail=f"Lead creation failed: {str(error)}"
        )

    connection.close()

    # 2. Automatically run the LOCAL AI analysis
    try:
        analysis_result = analyze_lead(lead_id)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Lead created but AI analysis failed: {str(error)}"
        )

    # 3. Get the fully updated lead
    connection = get_connection()

    row = connection.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    connection.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Lead was created but could not be retrieved"
        )

    return {
        "message": "Lead created and analyzed successfully 🤖🚀",
        "lead": dict(row),
        "analysis": analysis_result.get("analysis")
    }


# ==========================================
# GET ALL LEADS
# ==========================================

@app.get("/leads")
def get_all_leads():

    connection = get_connection()

    rows = connection.execute(
        "SELECT * FROM leads ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]

   
# ==========================================
# GET SINGLE LEAD
# ==========================================

@app.get("/leads/{lead_id}")
def get_lead(lead_id: int):

    connection = get_connection()

    row = connection.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    connection.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    return dict(row)


# ==========================================
# AI LEAD ANALYSIS
# ==========================================

@app.post("/leads/{lead_id}/analyze")
def analyze_lead(lead_id: int):

    connection = get_connection()

    row = connection.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    if not row:
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    lead = dict(row)

    connection.close()

    # Send lead information to AI
    ai_result = analyze_lead_with_ai(
        name=lead["name"],
        company=lead["company"],
        requirement=lead["requirement"],
        budget=lead["budget"]
    )

    # Default values
    lead_score = 0
    category = "General Enquiry"
    priority = "MEDIUM"
    intent = "General customer enquiry"
    recommended_action = "Follow up with customer"

    # Read AI response
    for line in ai_result.splitlines():

        line = line.strip()

        if line.startswith("LEAD_SCORE:"):
            try:
                lead_score = int(
                    line.split(":", 1)[1].strip()
                )
            except ValueError:
                pass

        elif line.startswith("CATEGORY:"):
            category = line.split(
                ":", 1
            )[1].strip()

        elif line.startswith("PRIORITY:"):
            priority = line.split(
                ":", 1
            )[1].strip().upper()

        elif line.startswith("INTENT:"):
            intent = line.split(
                ":", 1
            )[1].strip()

        elif line.startswith("RECOMMENDED_ACTION:"):
            recommended_action = line.split(
                ":", 1
            )[1].strip()

    # Keep score safe
    lead_score = max(
        0,
        min(lead_score, 100)
    )

    # Keep priority valid
    if priority not in ["HIGH", "MEDIUM", "LOW"]:
        priority = "MEDIUM"

    # Save AI analysis
    connection = get_connection()

    connection.execute(
        """
        UPDATE leads
        SET lead_score = ?,
            category = ?,
            priority = ?,
            recommended_action = ?
        WHERE id = ?
        """,
        (
            lead_score,
            category,
            priority,
            recommended_action,
            lead_id
        )
    )

    connection.commit()
    connection.close()

    return {
        "message": "Lead analyzed by AI successfully 🤖",
        "analysis": {
            "lead_id": lead_id,
            "customer": lead["name"],
            "lead_score": lead_score,
            "category": category,
            "priority": priority,
            "intent": intent,
            "recommended_action": recommended_action
        },
        "raw_ai_response": ai_result
    }
@app.get("/leads/{lead_id}/response")
def generate_response(lead_id: int):

    connection = get_connection()

    row = connection.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    connection.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    lead = dict(row)

    response = generate_customer_response(
        name=lead["name"],
        company=lead["company"],
        requirement=lead["requirement"],
        budget=lead["budget"],
        priority=lead["priority"],
        category=lead["category"]
    )

    return {
        "lead_id": lead_id,
        "customer": lead["name"],
        "suggested_response": response
    }
    connection = get_connection()

    row = connection.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    connection.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    lead = dict(row)

    response = generate_customer_response(
        name=lead["name"],
        company=lead["company"],
        requirement=lead["requirement"],
        budget=lead["budget"],
        priority=lead["priority"],
        category=lead["category"]
    )

    return {
        "lead_id": lead_id,
        "customer": lead["name"],
        "suggested_response": response
    }
@app.post("/leads/{lead_id}/approve")
def approve_lead_response(lead_id: int):

    connection = get_connection()

    row = connection.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    if not row:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    lead = dict(row)

    connection.execute(
        """
        UPDATE leads
        SET priority = COALESCE(priority, 'MEDIUM')
        WHERE id = ?
        """,
        (lead_id,)
    )

    connection.commit()
    connection.close()

    return {
        "message": "Response approved successfully ✅",
        "lead_id": lead_id,
        "status": "APPROVED",
        "next_action": "Ready to send to customer"
    }
@app.post("/leads/{lead_id}/send-email")
async def send_email_to_lead(lead_id: int):

    connection = get_connection()

    row = connection.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    connection.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    lead = dict(row)

    # Generate AI response
    ai_message = generate_customer_response(
        name=lead["name"],
        company=lead["company"],
        requirement=lead["requirement"],
        budget=lead["budget"],
        priority=lead["priority"],
        category=lead["category"]
    )

    # Send email
    try:
        await send_lead_email(
            customer_email=lead["email"],
            customer_name=lead["name"],
            message=ai_message
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Email sending failed: {str(error)}"
        )

    return {
        "message": "Email sent successfully 📧",
        "lead_id": lead_id,
        "customer": lead["name"],
        "email": lead["email"],
        "status": "SENT"
    }