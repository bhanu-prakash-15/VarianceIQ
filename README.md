VarianceIQ – FP&A Variance Copilot  
COT6930: Generative Intelligence & Software Development Lifecycles – Final Project*  
By: Bhanu Prakash Mudavath

---

Overview  

VarianceIQ is an AI-powered FP&A (Financial Planning & Analysis) assistant that automates **budget vs. actual variance analysis** using a multi-agent architecture.  
It combines deterministic numerical analytics with generative narrative explanations to support executive decision-making.

The system consists of:

**Analysis Agent (Python)**
- Computes absolute & percentage variances  
- Applies materiality thresholds  
- Classifies drivers (overspend / underspend / baseline)  
- Produces structured JSON output  

**Explanation Agent (Azure GPT-4o-mini)**
- Generates CFO-ready variance narratives  
- Summarizes top drivers and insights  
- Automatically falls back to a rule-based explainer if needed  

**Interactive Streamlit Dashboard**
- Upload budget datasets  
- Visualize department-level variance charts  
- Explore material line items  
- View generated AI-powered explanations  

---

Multi-Agent Architecture:

Upload CSV Dataset
Analysis Agent (deterministic) 
JSON Summary Explanation Agent (Azure GPT-4o-mini) 
Executive Narrative + Key Drivers 
Streamlit Dashboard (UI)

