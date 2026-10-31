# AGENTS.md — Autonomous Agent Operating Contract

## 🎯 Repository Purpose & Architecture
`enterprise-procurement-agent` is an enterprise multi-agent procurement copilot (LangGraph, MCP, Pinecone/Postgres, AWS Bedrock/Gemini, FastAPI, Streamlit) integrating SQL text-to-query generation, vendor contract risk assessment, guardrails-enforced policies, and automated purchase approval workflows.

### Tech Stack
- **Language**: Python 3.11+
- **Frameworks**: LangGraph, FastAPI, Streamlit, Pydantic v2
- **Testing**: Pytest

---

## ⚡ Autonomous Execution Protocol
1. Pull task from `TASKS.json`.
2. Adhere to procurement policy guardrails and schema validation.
3. Run verification: `pytest tests/`.
4. Commit with: `feat(task-id): description`.
