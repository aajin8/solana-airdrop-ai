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

    try:
        r = requests.get(url, headers=headers, params=params)
        data = r.json()

        if "web" not in data:
            return "Brave API error:\n" + str(data)

        return "\n".join(
            [item["title"] + " " + item.get("description", "")
             for item in data["web"]["results"]]
        )

    except Exception as e:
        return f"Brave request failed:\n{str(e)}"


def analyze_gemini(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API}"

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

    try:
        r = requests.post(url, json=body)
        data = r.json()

        if "candidates" not in data:
            return "Gemini API error:\n" + str(data)

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"Gemini request failed:\n{str(e)}"


def send_email(content):
    try:
        msg = MIMEText(content)
        msg["Subject"] = f"Solana Level5 AI Report {datetime.now().date()}"
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)

    except Exception as e:
        print("Email send failed:", str(e))


if __name__ == "__main__":
    search_result = search_brave()
    report = analyze_gemini(search_result)
    send_email(report)
