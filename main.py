import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

BRAVE_API = os.getenv("BRAVE_API_KEY")
GEMINI_API = os.getenv("GEMINI_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")


# -----------------------------
# 1. Brave Search
# -----------------------------
def search_brave():
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"X-Subscription-Token": BRAVE_API}
    params = {
        "q": "Solana Mobile Season 2 Level 5 XP guide new dapp airdrop strategy",
        "count": 5
    }

    r = requests.get(url, headers=headers, params=params)
    data = r.json()

    if "web" not in data or not data["web"].get("results"):
        return "No significant new updates found today regarding Solana Mobile."

    return "\n\n".join(
        [item["title"] + "\n" + item.get("description", "")
         for item in data["web"]["results"]]
    )


# -----------------------------
# 2. Gemini Analysis
# -----------------------------
def analyze_gemini(text):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API}"

    prompt = f"""
You are an elite Solana Mobile Season 2 Level5 strategist AI.

Analyze the information below and produce a structured report.

Return in this exact format:

⭐ Importance: (1-5)
🎯 Level5 Impact:
📈 XP Efficiency Insight:
🛠 Action Plan Today:
💰 Estimated Cost:
⚡ Execute Today? (YES/NO)
🧠 Risk Level:
📊 Farming Priority Score (1-100):

Focus on:
- New dapps inside Solana Mobile
- Airdrop farming potential
- XP optimization
- Season 2 Level5 progress acceleration

TEXT:
{text}
"""

    body = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }]
    }

    r = requests.post(url, json=body)
    data = r.json()

    if "candidates" not in data:
        return "Gemini API error:\n" + str(data)

    return data["candidates"][0]["content"]["parts"][0]["text"]


# -----------------------------
# 3. Send Email
# -----------------------------
def send_email(content):
    msg = MIMEText(content)
    msg["Subject"] = f"🔥 Solana Level5 AI Report {datetime.now().date()}"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)


# -----------------------------
# 4. Main Execution
# -----------------------------
if __name__ == "__main__":
    search_result = search_brave()
    report = analyze_gemini(search_result)
    send_email(report)
