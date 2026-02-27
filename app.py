import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import sqlite3
import bcrypt
from openai import OpenAI

# ---------------- CONFIG ----------------

MONDAY_API_KEY = st.secrets["MONDAY_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

DEALS_BOARD_ID = "5026890578"
WORK_BOARD_ID = "5026890612"

st.set_page_config(page_title="Monday BI Agent", layout="centered")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password BLOB,
    plan TEXT DEFAULT 'Free',
    credits INTEGER DEFAULT 3
)
""")
conn.commit()

# ---------------- AUTH FUNCTIONS ----------------
def register_user(username, password):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_pw)
        )
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode(), user[2]):
        return user
    return None

def update_user_data(username, credits, plan):
    cursor.execute(
        "UPDATE users SET credits = ?, plan = ? WHERE username = ?",
        (credits, plan, username)
    )
    conn.commit()

# ---------------- SESSION INIT ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- AUTH UI ----------------
if not st.session_state.logged_in:

    st.title("🔐 Login / Register")

    option = st.radio("Select Option", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Register":
        if st.button("Register"):
            if register_user(username, password):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username already exists.")

    if option == "Login":
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user[1]
                st.session_state.plan = user[3]
                st.session_state.credits = user[4]
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

    st.stop()

# ---------------- MAIN APP ----------------
st.title("📊 Monday.com Business Intelligence Agent")

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 👤 User Info")
st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
st.sidebar.write(f"Plan: **{st.session_state.plan}**")
st.sidebar.write(f"AI Credits: **{st.session_state.credits}**")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("## 💳 Upgrade Plans")

if st.sidebar.button("Buy 5 Credits (Pro)"):
    st.session_state.credits += 5
    st.session_state.plan = "Pro"
    update_user_data(st.session_state.username,
                     st.session_state.credits,
                     st.session_state.plan)
    st.sidebar.success("Upgraded to Pro!")

if st.sidebar.button("Buy 15 Credits (Enterprise)"):
    st.session_state.credits += 15
    st.session_state.plan = "Enterprise"
    update_user_data(st.session_state.username,
                     st.session_state.credits,
                     st.session_state.plan)
    st.sidebar.success("Upgraded to Enterprise!")

# ---------------- QUESTIONS ----------------
common_questions = [
    "How many work orders are pending?",
    "How many work orders are completed?",
    "Total number of work orders?",
    "What is our total pipeline value?",
    "What revenue have we closed?",
    "What is our conversion rate?",
    "Highest value deal?",
    "Lowest value deal?",
    "Average deal value?",
    "Total deals count?"
]

selected_question = st.selectbox(
    "Select a common business question:",
    ["-- Select --"] + common_questions
)

# ---------------- FETCH ----------------
def fetch_board_data(board_id):
    query = f"""
    {{
      boards(ids: {board_id}) {{
        items_page(limit: 500) {{
          items {{
            name
            column_values {{
              text
              column {{
                title
              }}
            }}
          }}
        }}
      }}
    }}
    """

    response = requests.post(
        "https://api.monday.com/v2",
        json={"query": query},
        headers={
            "Authorization": MONDAY_API_KEY,
            "Content-Type": "application/json"
        }
    )

    data = response.json()
    items = data["data"]["boards"][0]["items_page"]["items"]

    rows = []
    for item in items:
        row = {"Item Name": item["name"]}
        for col in item["column_values"]:
            row[col["column"]["title"]] = col["text"]
        rows.append(row)

    return pd.DataFrame(rows)

# ---------------- CLEAN ----------------
def clean_deals(df):
    if "Masked Deal value" in df.columns:
        df["Masked Deal value"] = (
            df["Masked Deal value"]
            .fillna("0")
            .str.replace(",", "")
            .str.replace("$", "")
        )
        df["Masked Deal value"] = pd.to_numeric(
            df["Masked Deal value"], errors="coerce"
        ).fillna(0)
    return df

def clean_work_orders(df):
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df

# ---------------- CALCULATIONS ----------------
def calculate_answer(question, deals_df, work_df):
    q = question.lower()

    if "pending" in q:
        return len(work_df[work_df["Execution Status"].str.contains("pending", case=False, na=False)])

    if "completed" in q:
        return len(work_df[work_df["Execution Status"].str.contains("complete", case=False, na=False)])

    if "pipeline" in q:
        return deals_df["Masked Deal value"].sum()

    if "conversion rate" in q:
        total = len(deals_df)
        closed = len(deals_df[deals_df["Deal Status"].str.contains("closed", case=False, na=False)])
        return round((closed / total * 100), 2) if total > 0 else 0

    if "highest value" in q:
        return deals_df["Masked Deal value"].max()

    if "lowest value" in q:
        return deals_df["Masked Deal value"].min()

    if "average deal value" in q:
        return round(deals_df["Masked Deal value"].mean(), 2)

    if "total deals count" in q:
        return len(deals_df)

    return "Calculation not defined."

# ---------------- AI INSIGHT ----------------
def generate_ai_insight(question, direct_result):

    prompt = f"""
You are a strategic executive advisor.

The system calculated:

Direct Answer: {direct_result}

Provide executive-level insight for:
{question}

Use the direct answer provided.
Do not recalculate numbers.
Add strategic recommendations.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# ---------------- EXECUTION ----------------
if selected_question != "-- Select --":

    st.write("🔄 Fetching live data...")
    deals_df = clean_deals(fetch_board_data(DEALS_BOARD_ID))
    work_df = clean_work_orders(fetch_board_data(WORK_BOARD_ID))

    st.subheader("📊 Direct BI Answer")
    direct_result = calculate_answer(selected_question, deals_df, work_df)
    st.write(direct_result)

    if st.button("🤖 Generate AI Executive Insight (Uses 1 Credit)"):
        if st.session_state.credits > 0:
            st.session_state.credits -= 1
            update_user_data(
                st.session_state.username,
                st.session_state.credits,
                st.session_state.plan
            )

            st.write("🤖 Thinking...")
            ai_result = generate_ai_insight(
                selected_question,
                direct_result
            )

            st.subheader("📈 AI Executive Insight")
            st.write(ai_result)
        else:
            st.error("No AI credits remaining.")