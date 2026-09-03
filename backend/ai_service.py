def analyze_lead_with_ai(name, company, requirement, budget):
    """
    Local AI-style lead scoring engine.
    No OpenAI API, no n8n, no internet required.
    """

    requirement_text = (requirement or "").lower()
    company_text = (company or "").lower()

    score = 40

    # Budget scoring
    if budget:
        if budget >= 100000:
            score += 30
        elif budget >= 75000:
            score += 25
        elif budget >= 50000:
            score += 20
        elif budget >= 25000:
            score += 10

    # High-value requirements
    high_value_keywords = [
        "website",
        "web development",
        "application",
        "app",
        "software",
        "ecommerce",
        "e-commerce",
        "ai",
        "automation",
        "dashboard",
        "crm"
    ]

    matched_keywords = [
        word for word in high_value_keywords
        if word in requirement_text
    ]

    score += min(len(matched_keywords) * 5, 20)

    # Company provided
    if company_text:
        score += 5

    # Keep score between 0 and 100
    score = max(0, min(score, 100))

    # Priority
    if score >= 80:
        priority = "HIGH"
    elif score >= 55:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    # Category
    if any(word in requirement_text for word in ["website", "web", "ecommerce"]):
        category = "Web Development"
    elif any(word in requirement_text for word in ["app", "application", "android", "mobile"]):
        category = "App Development"
    elif any(word in requirement_text for word in ["ai", "automation", "machine learning"]):
        category = "AI & Automation"
    elif any(word in requirement_text for word in ["software", "crm"]):
        category = "Software Development"
    else:
        category = "General Enquiry"

    # Intent
    if score >= 80:
        intent = "Strong purchase intent"
    elif score >= 55:
        intent = "Moderate purchase intent"
    else:
        intent = "Early-stage enquiry"

    # Recommended action
    if priority == "HIGH":
        recommended_action = "Contact customer immediately and schedule a discussion"
    elif priority == "MEDIUM":
        recommended_action = "Follow up with customer and collect more requirements"
    else:
        recommended_action = "Keep lead engaged and follow up later"

    return f"""LEAD_SCORE: {score}
CATEGORY: {category}
PRIORITY: {priority}
INTENT: {intent}
RECOMMENDED_ACTION: {recommended_action}"""


def generate_customer_response(
    name,
    company,
    requirement,
    budget,
    priority,
    category
):
    """
    Local customer-response generator.
    No OpenAI API required.
    """

    company_text = company if company else "your company"

    budget_text = (
        f"₹{budget:,.0f}"
        if budget
        else "the budget discussed"
    )

    response = f"""Hi {name},

Thank you for contacting LEADFLOW AI regarding your requirement.

We understand that you are looking for:

{requirement}

We would be happy to discuss how we can help {company_text} with this requirement.

Based on the information provided:

- Category: {category or "General Enquiry"}
- Priority: {priority or "MEDIUM"}
- Budget: {budget_text}

We would like to understand a few more details so that we can suggest the most suitable solution.

Please let us know a convenient time for a quick discussion.

Best regards,
LEADFLOW AI Team
"""

    return response.strip()