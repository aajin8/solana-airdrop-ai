import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

BRAVE_API = os.getenv("BRAVE_API_KEY")
GEMINI_API = os.getenv("GEMINI_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")


def search_brave():
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "X-Subscription-Token": BRAVE_API
    }
    params = {
        "q": "Solana Mobile Season 2 Level 5 XP strategy OR new dapp OR airdrop update",
        "freshness": "pd",
        "count": 5
    }

    r = requests.get(url, headers=headers, params=params)
    data = r.json()

    if "web" not in data:
        return "Brave API error:\n" + str(data)

    return "\n".join(
        [item["title"] + " " + item.get("description", "")
         for item in data["web"]["results"]]
    )


def analyze_gemini(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={GEMINI_API}"

    body = {
        "contents": [{
            "parts": [{
                "text": f"""
Analyze this information for Solana Mobile Season 2.

Give:
1. Importance (1-5 stars)
2. Level5 impact
3. What action to take today
4. Estimated cost
5. Execute today? Yes/No

TEXT:
{text}
"""
            }]
        }]
    }

    r = requests.post(url, json=body)
    data = r.json()

    if "candidates" not in data:
        return "Gemini API error:\n" + str(data)

    return data["candidates"][0]["content"]["parts"][0]["text"]


def send_email(content):
    msg = MIMEText(content)
    msg["Subject"] = f"Solana Level5 AI Report {datetime.now().date()}"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)


if __name__ == "__main__":
    search_result = search_brave()
    report = analyze_gemini(search_result)
    send_email(report)
