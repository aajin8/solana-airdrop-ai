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
# Gemini戦略分析
# -----------------------------
def analyze(text):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API}"

    prompt = f"""
あなたはSeason2攻略専門の戦略AI。

ニュース要約は禁止。
戦略分析のみ出力。

JSONのみ返す：

{{
"alpha_signal_strength": 0-100,
"early_advantage": 0-100,
"allocation_impact": 0-100,
"behavior_shift_detected": true/false,
"season2_intent": "Season2の評価軸推定",
"strategic_play": "今日やるべき具体戦略",
"risk_note": "注意点"
}}

{text}
"""

    body = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3
        }
    }

    r = requests.post(url, json=body)
    response_json = r.json()

    if "candidates" not in response_json:
        raise Exception(f"Gemini API Error: {response_json}")

    raw = response_json["candidates"][0]["content"]["parts"][0]["text"]

    start = raw.find("{")
    end = raw.rfind("}") + 1

    if start == -1 or end == -1:
        raise ValueError("JSONが検出できません")

    return json.loads(raw[start:end])


# -----------------------------
# 状態管理
# -----------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"history": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# -----------------------------
# 総合判定
# -----------------------------
def calculate_score(data, state):
    score = (
        data["alpha_signal_strength"] * 0.4 +
        data["early_advantage"] * 0.2 +
        data["allocation_impact"] * 0.3
    )

    if data["behavior_shift_detected"]:
        score += 10

    score = round(min(100, score), 1)

    state["history"].append(score)

    prev = state["history"][-2] if len(state["history"]) > 1 else score
    diff = round(score - prev, 1)

    return score, diff


# -----------------------------
# メール生成（戦略のみ）
# -----------------------------
def build_email(data, score, diff):
    emergency = "【環境変化検出】" if data["behavior_shift_detected"] else ""
    spike = "【急騰】" if diff >= 15 else ""

    content = f"""
{emergency}{spike}🔥 Season2 戦略AI

【Alpha強度】{data["alpha_signal_strength"]}
【先行者優位度】{data["early_advantage"]}
【Allocation影響度】{data["allocation_impact"]}
【環境変化】{data["behavior_shift_detected"]}

【総合戦略スコア】{score}
【前日差】{diff}

🧠 Season2意図推定
{data["season2_intent"]}

🎯 今日の最適戦略
{data["strategic_play"]}

⚠ リスク
{data["risk_note"]}
"""

    return content


# -----------------------------
# メール送信
# -----------------------------
def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = f"Season2戦略AI {datetime.now().date()}"
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

    email = build_email(analysis, score, diff)

    send_email(email)

    save_state(state)
