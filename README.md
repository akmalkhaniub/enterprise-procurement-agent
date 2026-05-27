# Enterprise Procurement Agent

A multi-agent procurement workspace driven by Streamlit, FastAPI, LangChain, and Google's Gemini models. It uses an SQLite database for structured procurement logging and Chroma DB for vector search/RAG indexing of corporate policies.

## Tech Stack
- **Frontend:** Streamlit
- **Backend API:** FastAPI
- **Agent Orchestration:** LangChain / Custom Agent Tooling
- **Database:** SQLite (structured data)
- **Vector Index:** Chroma DB (retrieval augmented generation)
- **LLM Integration:** Google Gemini API

## Setup Instructions

### 1. Create a Virtual Environment
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

### 3. Setup Configuration
Copy `.env.example` to `.env` and fill in your Gemini API key:
```bash
cp .env.example .env
```

### 4. Initialize Databases
Initialize the SQLite schema and the Chroma DB vector store:
```bash
python setup_db.py
python setup_vector_db.py
```

## Running the Project

### 1. Start the Backend FastAPI App
```bash
python main.py
```
This launches the FastAPI server and the Model Context Protocol (MCP) server endpoint at `http://localhost:8080`.

### 2. Run the Streamlit Interface
In a separate terminal (with virtual env active):
```bash
streamlit run streamlit_app.py
```

## Project Files
- `streamlit_app.py`: Interactive user dashboard for executing agent goals.
- `main.py`: Main FastAPI entrypoint hosting the server.
- `agents.py`: LangChain agent definition and tools for managing purchase orders, requisitions, and vendor queries.
- `mcp_server.py`: Model Context Protocol integration.
- `setup_db.py`: Database tables creation and sample procurement records insertion.
- `setup_vector_db.py`: Ingestion scripts for corporate policies and RAG vector search indexing.
