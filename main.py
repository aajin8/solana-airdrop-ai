import requests
import smtplib
import os
import json
from email.mime.text import MIMEText
from datetime import datetime

BRAVE_API = os.getenv("BRAVE_API_KEY")
GEMINI_API = os.getenv("GEMINI_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")


# -----------------------------
# 1-A. Brave Web広域検索
# -----------------------------
def search_web():
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"X-Subscription-Token": BRAVE_API}

    query = """
    Solana Mobile Season 2 Level 5 XP
    Solana Seeker SKR allocation
    Solana new dapp release
    """

    params = {"q": query, "count": 6}
    r = requests.get(url, headers=headers, params=params)
    data = r.json()

    if "web" not in data or not data["web"].get("results"):
        return ""

    return "\n\n".join(
        [item["title"] + "\n" + item.get("description", "")
         for item in data["web"]["results"]]
    )


# -----------------------------
# 1-B. X本気モード監視（24h重視）
# -----------------------------
def search_x():
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"X-Subscription-Token": BRAVE_API}

    x_query = """
    site:twitter.com
    ("Solana Mobile" OR "Seeker" OR "SKR allocation" OR "Season 2")
    (announced OR live OR now OR airdrop OR allocation OR XP)
    """

    params = {
        "q": x_query,
        "count": 6,
        "freshness": "pd"   # past day
    }

    r = requests.get(url, headers=headers, params=params)
    data = r.json()

    if "web" not in data or not data["web"].get("results"):
        return ""

    return "\n\n".join(
        [item["title"] + "\n" + item.get("description", "")
         for item in data["web"]["results"]]
    )


# -----------------------------
# 2. Gemini分析（JSON数値）
# -----------------------------
def analyze_gemini(text):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API}"

    prompt = f"""
あなたはSolana Mobile Season2 レベル5専用評価AIです。

以下を分析し、JSONのみで返してください。

{{
  "new_dapp_score": 0-25,
  "xp_score": 0-20,
  "skr_score": 0-20,
  "freshness_score": 0-15,
  "risk_adjustment": -10 to +10,
  "reason_summary": "日本語で簡潔に理由"
}}

速報性が高いX情報はfreshness_scoreを強く評価。
レベル5到達に直結しない情報は減点。

情報:
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
        return None, "Gemini APIエラー"

    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

    try:
        json_start = raw_text.find("{")
        json_data = json.loads(raw_text[json_start:])
        return json_data, None
    except:
        return None, "JSON解析失敗\n" + raw_text


# -----------------------------
# 3. L5スコア計算（速報ブースト）
# -----------------------------
def calculate_l5_score(data, x_text):
    total = (
        data["new_dapp_score"] +
        data["xp_score"] +
        data["skr_score"] +
        data["freshness_score"] +
        data["risk_adjustment"]
    )

    # X速報ブースト（攻め）
    if any(word in x_text.lower() for word in ["announced", "live", "allocation", "airdrop"]):
        total += 5

    total = max(0, min(100, total))
    acceleration = round(total * 0.05, 2)

    if total >= 80:
        tier = "高"
    elif total >= 60:
        tier = "中"
    else:
        tier = "低"

    return total, acceleration, tier


# -----------------------------
# 4. メール構築
# -----------------------------
def build_email(data, total, acceleration, tier):
    return f"""
🔥 L5-Alpha Model 本気モード {datetime.now().date()}

【L5総合スコア】{total} / 100
【レベル5加速指数】+{acceleration}%
【Sovereign寄与】{tier}

新規dApp: {data['new_dapp_score']}
XP加速: {data['xp_score']}
SKR関連: {data['skr_score']}
速報性: {data['freshness_score']}
リスク補正: {data['risk_adjustment']}

--- 総評 ---
{data['reason_summary']}

戦略:
{"🔥 本日優先行動" if total >= 70 else "調査継続"}
"""


# -----------------------------
# 5. メール送信
# -----------------------------
def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = f"🔥 L5本気モード {datetime.now().date()}"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)


# -----------------------------
# 実行
# -----------------------------
if __name__ == "__main__":
    web_text = search_web()
    x_text = search_x()
    combined = web_text + "\n\n" + x_text

    analysis, error = analyze_gemini(combined)

    if error:
        send_email(error)
    else:
        total, acceleration, tier = calculate_l5_score(analysis, x_text)
        email_body = build_email(analysis, total, acceleration, tier)
        send_email(email_body)
