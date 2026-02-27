📊 Monday.com AI Business Intelligence Agent
🚀 Overview

This project is an AI-powered Business Intelligence Agent built for founders and executives to query business data across multiple monday.com boards in real time.

The system integrates with:

monday.com (Live API)

Groq Cloud LLM (Llama 3.1)

SQLite (User Authentication & Credit Management)

Streamlit (Frontend Interface)

It enables users to ask strategic business questions and receive:

Direct calculated BI answers

Optional AI-generated executive insights

🧠 Core Features
✅ Live monday.com Integration

Fetches board data at query time

No caching or preloading

Uses GraphQL API

✅ Data Cleaning & Normalization

Handles missing values

Cleans revenue formats

Normalizes status fields

Converts numeric fields properly

✅ Conversational BI Interface

Dropdown of common executive queries

Real-time computed metrics

Executive AI insight option

✅ AI Executive Insights (Groq LLM)

Uses llama-3.1-70b-versatile

Credit-based AI access

Strategic analysis layer

Does not recompute raw metrics

✅ Authentication System

User registration & login

Secure password hashing (bcrypt)

SQLite-backed persistence

Credit-based plan system

🏗 Architecture

User → Streamlit UI →
Live monday.com API →
Data Cleaning (Pandas) →
Direct BI Calculation →
(Optional) Groq LLM Insight →
Executive Response

💳 Credit System

Users start with free credits.

Plans:

Free

Pro

Enterprise

AI insights consume 1 credit per request.

🛠 Tech Stack

Python

Streamlit

Pandas

Requests

Groq API (OpenAI-compatible)

SQLite

bcrypt

🔐 Environment Variables

On deployment (Streamlit Cloud), configure:

MONDAY_API_KEY = your_monday_api_key
GROQ_API_KEY = your_groq_api_key

Secrets are configured via Streamlit Cloud Secrets Manager.

📦 Installation (Local)
pip install -r requirements.txt
streamlit run app.py
🌐 Deployment

Deployed using Streamlit Cloud.

No local dependencies required.

🎯 Sample Questions

How many work orders are pending?

What is our total pipeline value?

What is our conversion rate?

Highest value deal?

Average deal value?

🧩 Design Decisions

Python handles all numeric calculations.

LLM only provides strategic interpretation.

No dataset is directly passed to LLM.

SQLite used for lightweight authentication demo.

Cloud-based LLM chosen for deployability.

📌 Notes

SQLite is used for demo authentication purposes.

In production, a managed database (PostgreSQL) would be recommended.

The system is designed to be scalable and model-agnostic.

👨‍💻 Author

Built as a Business Intelligence AI prototype integrating live enterprise data with cloud-based large language models.

