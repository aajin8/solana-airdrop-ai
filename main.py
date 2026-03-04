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

STATE_FILE = "state.json"


# -----------------------------
# Brave検索
# -----------------------------
def brave_search(query, freshness=None):
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"X-Subscription-Token": BRAVE_API}
    params = {"q": query, "count": 5}
    if freshness:
        params["freshness"] = freshness

    r = requests.get(url, headers=headers, params=params)
    data = r.json()

    if "web" not in data or not data["web"].get("results"):
        return ""

    return "\n\n".join(
        [item["title"] + "\n" + item.get("description", "")
         for item in data["web"]["results"]]
    )


def gather_data():
    web = brave_search("Solana Mobile Season2 SKR XP allocation new dapp")
    x = brave_search("""
    site:twitter.com/solanamobile OR
    site:twitter.com/solana OR
    site:twitter.com/solanafloor
    """, freshness="pd")

    return web + "\n\n" + x


# -----------------------------
# Gemini分析＋行動提案
# -----------------------------
def analyze(text):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API}"

    prompt = f"""
Solana Mobile Season2 レベル5専用AI。

JSONのみ出力：

{{
"scores": {{
  "new_dapp": 0-25,
  "xp": 0-20,
  "skr": 0-20,
  "freshness": 0-15,
  "risk": -10 to +10
}},
"dapps": ["dApp名"],
"keywords": ["重要語句"],
"summary": "日本語要約",
"action_plan": "今日やるべき具体的行動"
}}

{text}
"""

    body = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }]
    }

    r = requests.post(url, json=body)
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw[raw.find("{"):])


# -----------------------------
# 状態管理
# -----------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"history": [], "dapp_counts": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# -----------------------------
# スコア計算
# -----------------------------
def calculate_score(data, state):
    s = data["scores"]
    total = s["new_dapp"] + s["xp"] + s["skr"] + s["freshness"] + s["risk"]
    total = max(0, min(100, total))

    # dApp出現回数更新
    for d in data["dapps"]:
        state["dapp_counts"][d] = state["dapp_counts"].get(d, 0) + 1

    state["history"].append(total)

    prev = state["history"][-2] if len(state["history"]) > 1 else total
    diff = total - prev

    return total, diff


# -----------------------------
# SKRレンジ推定
# -----------------------------
def skr_range(score):
    if score >= 80:
        return "500k〜750k（Sovereign帯）"
    elif score >= 60:
        return "250k〜500k"
    else:
        return "〜250k"


# -----------------------------
# メール作成
# -----------------------------
def build_email(data, score, diff, state):
    ranking = sorted(state["dapp_counts"].items(), key=lambda x: x[1], reverse=True)[:5]
    ranking_text = "\n".join([f"{r[0]} ({r[1]}回)" for r in ranking])

    emergency = "【緊急】" if diff >= 15 else ""

    return f"""
{emergency}🔥 L5戦略AI V3 {datetime.now().date()}

【本日スコア】{score}
【前日差】{diff}
【予想SKRレンジ】{skr_range(score)}

🔥 注目dAppランキング
{ranking_text}

--- 要約 ---
{data["summary"]}

🎯 今日の行動提案
{data["action_plan"]}
""", emergency


# -----------------------------
# メール送信
# -----------------------------
def send_email(content, emergency):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = f"{emergency}L5戦略AI {datetime.now().date()}"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)


# -----------------------------
# 実行
# -----------------------------
if __name__ == "__main__":
    state = load_state()
    text = gather_data()
    analysis = analyze(text)

    score, diff = calculate_score(analysis, state)
    email, emergency = build_email(analysis, score, diff, state)

    send_email(email, emergency)
    save_state(state)
