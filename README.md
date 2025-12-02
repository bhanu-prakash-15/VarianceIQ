---

# **VarianceIQ – FP&A Variance Intelligence System**

### *COT6930: Generative Intelligence & Software Development Lifecycles – Final Project*

**By: Bhanu Prakash Mudavath**

---

# 📌 **Overview**

**VarianceIQ** is an AI-powered FP&A (Financial Planning & Analysis) system that automates **Budget vs. Actual variance analysis**, generates **executive-ready explanations**, and provides **forecasting guidance** using a **multi-agent Generative Intelligence architecture**.

It combines:

* **Deterministic numerical analysis**
* **Generative narrative explanations (LLM)**
* **AI-driven forecasting suggestions**
* **Interactive Streamlit UI with login & per-user history**

This solution drastically reduces time spent on manual FP&A tasks, delivering fast, accurate, and decision-ready insights.

---

# 🚀 **Core System Features**

## **1️⃣ Analysis Agent (Deterministic Engine)**

Built in Python, this agent processes uploaded budget datasets and produces structured insights:

* Computes absolute & percentage variances
* Identifies favorable / unfavorable drivers
* Applies materiality thresholds
* Aggregates results by department
* Produces structured **JSON summaries** for downstream agents

---

## **2️⃣ Explanation Agent (Azure GPT-4o-mini)**

Translates raw calculations into CFO-ready narratives:

* Executive summaries
* Top variance drivers
* Clear, concise explanations
* Works in two modes:
  ✔ **LLM Mode (Azure GPT-4o-mini)**
  ✔ **Rule-Based Mode (Fallback)**

---

## **3️⃣ Forecasting Agent (LLM-Based & Rule-Based Hybrid)**

Provides forward-looking recommendations including:

* What departments should adjust next month
* Which spending areas may continue to deviate
* Budget optimization suggestions
* Actions to reduce variance and stay aligned with plan

Works in two modes:

* **LLM Mode** → Deep reasoning + tailored recommendations
* **Rule-Based Mode** → Deterministic fallback

---

## **4️⃣ Chat-Style Interaction (Assistant Panel)**

Once a user uploads a dataset:

* Users can ask natural-language questions:

  * “Why is variance high this month?”
  * “Which department overspent the most?”
  * “What should we do to reduce variance next month?”
* Assistant responds using the **Explanation Agent + Forecasting Agent**
* Behaves like ChatGPT but grounded in your uploaded financial data

---

## **5️⃣ Full Streamlit Dashboard (PowerBI-style)**

* Modern UI with custom CSS
* Upload CSV/XLSX
* Interactive plots & KPIs
* AI-generated narratives
* Forecasting suggestions
* Run History per user
* Login / Signup with persistent accounts

---

# 🧠 **Multi-Agent Architecture**

```
            ┌────────────────────┐
            │   User Uploads File │
            └───────────┬────────┘
                        ↓
            ┌────────────────────┐
            │  Analysis Agent     │
            │ (Deterministic)     │
            └───────────┬────────┘
                        ↓
            ┌────────────────────┐
            │ JSON Summary        │
            └───────────┬────────┘
                        ↓
      ┌────────────────────────────────────┐
      │     Multi-Agent Generative Layer    │
      │  ┌──────────────────────────────┐   │
      │  │ Explanation Agent (LLM)      │   │
      │  └──────────────────────────────┘   │
      │  ┌──────────────────────────────┐   │
      │  │ Forecasting Agent (LLM)      │   │
      │  └──────────────────────────────┘   │
      └──────────────────┬─────────────────┘
                         ↓
            ┌────────────────────┐
            │ Streamlit UI       │
            │ Dashboard + Chat   │
            └────────────────────┘
```

---

# 🛠 **Technology Stack**

| Component              | Technology                             |
| ---------------------- | -------------------------------------- |
| Frontend UI            | Streamlit + Custom CSS                 |
| Backend Logic          | Python 3.10                            |
| LLM Models             | Azure GPT-4o-mini                      |
| Charts & Visualization | Plotly Express                         |
| Authentication         | CSV-based login system                 |
| Storage Layer          | JSON-based per-user history            |
| Agents Framework       | Custom multi-agent Python architecture |
| Chat Interface         | Streamlit chat + agent routing         |

---

# 📁 **Project Structure**

```
├── app.py                     # Main Streamlit application (UI + orchestration)
├── analysis_agent.py          # Deterministic variance computation agent
├── explanation_agent.py       # LLM-powered narrative agent
├── forecasting_agent.py       # Forecasting guidance agent
├── users.csv                  # Login credentials
├── user_history/              # Per-user run history JSON files
├── uploaded_files/            # Saved uploaded datasets
├── assets/                    # Screenshots, architecture diagram
├── requirements.txt           # Dependencies
└── README.md                  # Documentation
```

---

# ⚙️ **How to Run Locally**

### **1. Install dependencies**

```bash
pip install -r requirements.txt
```

### **2. Start application**

```bash
streamlit run app.py
```

### **3. Open in browser**

```
http://localhost:8501
```

---

# 🔐 **Authentication & User History**

* Each user logs in with email + password
* Entire history is stored **per user**
* Users cannot view each other's runs
* History includes:

  * Run ID
  * Timestamp
  * KPIs
  * File uploaded
  * Executive narrative
  * Key points
  * Forecasting suggestions
  * Chat queries (optional)

---

# 📂 **Dataset Assets**

VarianceIQ relies on real-world public-sector financial data.
For demonstration and evaluation, the following datasets are provided:

### **✔ Demo Budget Dataset (CSV, ~45MB)**

A structured subset used during testing and interface demonstration.
🔗 [https://drive.google.com/file/d/1SPwln0DuizH-Mw3JbA-_mId6gBwirDUP/view?usp=drive_link](https://drive.google.com/file/d/1SPwln0DuizH-Mw3JbA-_mId6gBwirDUP/view?usp=drive_link)

### **✔ NYC Expense Budget — Full Dataset (CSV, ~270MB)**

Official dataset used for full-scale budget variance analysis.
🔗 [https://drive.google.com/file/d/1TSPdi6rTLS-29iUDC-ZCFdQAWUT7YXoJ/view?usp=drive_link](https://drive.google.com/file/d/1TSPdi6rTLS-29iUDC-ZCFdQAWUT7YXoJ/view?usp=drive_link)

---

# 🎯 **Why This Project Matters**

VarianceIQ demonstrates:

### **Real-world application of Generative AI**

Transforming raw numerical data into narratives and forecast guidance.

### **Multi-agent workflow design**

Each agent handles a different cognitive task, like a digital FP&A team.

### **Human-in-the-loop FP&A augmentation**

Analyst reviews and refines final explanations.

### **Automation of repetitive financial tasks**

Reduces variance explanation time by up to **80%**.

### **Business value + technical depth**

Fits both academic and real-world FP&A use cases.

---


