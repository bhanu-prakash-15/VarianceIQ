

# **VarianceIQ – FP&A Variance **

### *COT6930: Generative Intelligence & Software Development Lifecycles – Final Project*

**By: Bhanu Prakash Mudavath**

---

## 📌 **Overview**

**VarianceIQ** is an AI-powered FP&A (Financial Planning & Analysis) assistant designed to automate **Budget vs. Actual variance analysis** using a **multi-agent architecture**.
It combines **deterministic numerical processing** with **generative executive-level narrative explanations**, enabling rapid, data-driven insights for finance teams.

---

## 🚀 **Key Features**

### **1. Analysis Agent (Python – Deterministic Engine)**

Processes the uploaded budget dataset and generates structured quantitative insights:

* Computes absolute & percentage variances
* Applies materiality thresholds
* Detects favorable / unfavorable / neutral drivers
* Aggregates insights by department
* Outputs machine-readable **JSON summary**

---

### **2. Explanation Agent (Azure GPT-4o-mini)**

Transforms numeric output into CFO-style narratives:

* Generates executive summaries
* Highlights top variance drivers
* Writes concise, formal, professional explanations
* Automatic fallback to a **rule-based explainer** when LLM mode is off

---

### **3. Streamlit Interactive Dashboard**

A modern, PowerBI-style interface to explore insights:

* Upload CSV/XLSX budget datasets
* View total budget, expenses, variance KPIs
* Visualize spending and variance using bar & donut charts
* Review generated AI explanations
* Per-user **Run History** with uploaded files & generated narratives
* Login / Signup with persistent user-specific history

---

## 🧠 **Multi-Agent Workflow**

```
Upload Budget File (.csv/.xlsx)
          ↓
Analysis Agent (Deterministic Python Engine)
          ↓
Structured Variance Summary (JSON)
          ↓
Explanation Agent (Azure GPT-4o-mini)
          ↓
Executive Narrative + Key Drivers
          ↓
VarianceIQ Streamlit Dashboard (UI)
```

---

## 🛠️ **Technology Stack**

| Component                 | Technology                                 |
| ------------------------- | ------------------------------------------ |
| Frontend UI               | Streamlit (custom CSS themed like PowerBI) |
| Backend Logic             | Python 3.10                                |
| LLM Model                 | Azure GPT-4o-mini                          |
| Visualization             | Plotly Express                             |
| Authentication            | CSV-based login system                     |
| Data Storage              | Per-user JSON history store                |
| Multi-Agent Orchestration | Custom Python classes                      |

---

## 📂 **Project Structure**

```
├── app.py                     # Streamlit main app
├── analysis_agent.py          # Deterministic analysis agent
├── explanation_agent.py       # GPT-4o-mini narrative generator
├── users.csv                  # Login system storage
├── user_history/              # Per-user history JSON files
├── uploaded_files/            # User-uploaded datasets
├── README.md                  # Project documentation
```

---

## ⚙️ **How to Run**

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit app:

```bash
streamlit run app.py
```

Open in browser:

```
http://localhost:8501
```

---

## 🔐 **User Accounts & History**

* Each user has their own login
* All analyses are saved in **run history**
* Each history item includes:

  * Run ID
  * Timestamp
  * Summary KPIs
  * Uploaded file link
  * Executive Narrative
  * Key Points

No user can see another user’s history.

---

## 🎯 **Purpose**

This project demonstrates the application of **Generative AI in Financial Analytics**, focusing on:

* AI agents collaboration
* Narrative financial reporting
* Automation of repetitive FP&A workflows
* Interactive analytical dashboards

---



