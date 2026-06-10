# 🛒 Enterprise Procurement Agent

<p align="center">
  <img src="https://img.shields.io/badge/Streamlit-Supported-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/FastAPI-Python%203.10-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/LangChain-Orchestrator-000000?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/Chroma%20DB-Vector%20Search-orange?style=for-the-badge" alt="Chroma DB">
  <img src="https://img.shields.io/badge/Google%20Gemini-API-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/SQLite-Supported-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License MIT">
</p>

An intelligent, multi-agent procurement workspace driven by Streamlit, FastAPI, LangChain, and Google's Gemini models. This workspace coordinates purchasing compliance audits, vendor query resolutions, and automated purchase order generations. It leverages an SQLite database for structured tracking and Chroma DB for vector search/RAG indexing of corporate policy guides.

---

## 🎨 System Architecture

```mermaid
graph TD
    classDef client fill:#f3e8ff,stroke:#7c3aed,stroke-width:2px,color:#5b21b6;
    classDef gateway fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef agent fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#9a3412;
    classDef db fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#166534;
    classDef ai fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#991b1b;

    UI["💻 Streamlit Dashboard"] -->|HTTP API| Server["Backend API Gateway (FastAPI)"]
    
    Server --> Swarm
    
    subgraph Swarm [LangChain Agent Swarm]
        PurchasingAgent["📋 Requisition Agent"]
        VendorAgent["💬 Vendor Query Agent"]
        ComplianceAgent["🛡️ Policy Audit Agent"]
    end
    
    Swarm <-->|SQL Log| SQLite[("SQLite Procurement DB")]
    Swarm <-->|RAG Query| Chroma[("Chroma DB Policy Store")]
    Swarm -->|Inference| Gemini["Google Gemini API"]

    class UI client;
    class Server gateway;
    class PurchasingAgent,VendorAgent,ComplianceAgent agent;
    class SQLite,Chroma db;
    class Gemini ai;
    
    style Swarm fill:#f8fafc,stroke:#cbd5e1,stroke-width:1px,stroke-dasharray: 5 5;
```

---

## ✨ Key Features

*   **Multi-Agent Coordination**: Employs LangChain custom agents specialized in Requisition Routing, Vendor Query Resolution, and Compliance Audit checks.
*   **Structured Logging**: SQLite transaction management for tracking purchase order stages, requisition updates, and vendor communication details.
*   **Corporate Policy RAG**: Vector similarity search using Chroma DB over ingested PDF procurement manuals, ensuring all requisitions comply with standard corporate budget guidelines.
*   **Model Context Protocol (MCP)**: Dynamic tool integration exposed through FastAPI endpoints to query live models.
*   **Interactive Streamlit Panel**: Easy-to-use client interface for tracking agent execution logs, viewing policy search hits, and creating orders.

---

## 🛠 Tech Stack

-   **Frontend**: Streamlit
-   **Backend Gateway**: FastAPI · Uvicorn
-   **Agent Framework**: LangChain
-   **Structured DB**: SQLite (SQLAlchemy connection)
-   **Vector Index**: Chroma DB (Retrieval-Augmented Generation)
-   **LLM Provider**: Google Gemini API

---

## 🚀 Getting Started

### 1. Setup Virtual Environment
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your `GEMINI_API_KEY` (Get one free at [Google AI Studio](https://aistudio.google.com/)).

### 4. Initialize Databases
Initialize SQLite schema and Chroma DB vector indexes:
```bash
python setup_db.py
python setup_vector_db.py
```

### 5. Running the Application

#### Start the FastAPI Server
```bash
python main.py
```
FastAPI backend and MCP server start at `http://localhost:8080`.

#### Start the Streamlit Client
In a new terminal (with virtual environment active):
```bash
streamlit run streamlit_app.py
```

---

## 📂 Project Structure

*   `streamlit_app.py`: Streamlit control panel interface.
*   `main.py`: FastAPI server configuration hosting backend API.
*   `agents.py`: LangChain multi-agent definition and tools mapping.
*   `mcp_server.py`: Model Context Protocol tool implementation.
*   `setup_db.py`: Database table generation and mockup values ingestion.
*   `setup_vector_db.py`: Ingests PDF manuals into Chroma DB vector embeddings.

---

## 🏁 License & Contact

Distributed under the MIT License. See `LICENSE` for more information.

*Project Lead: Akmal Khan*  
*Email: akmal.shahbaz@iub.edu.pk*  
*Repository Link: [https://github.com/akmalkhaniub/enterprise-procurement-agent](https://github.com/akmalkhaniub/enterprise-procurement-agent)*
