# Google Cloud Professional Agentic Architect: Production Improvement Plan
## Repository: enterprise-procurement-agent
**Audit Date:** November 6, 2026  
**Target Standard:** Google Cloud Professional Agentic Architect (Domain 3: Custom Agents & Domain 5: Security Governance)

---

### Current Assessment
An enterprise multi-agent procurement copilot (LangGraph, MCP, ChromaDB, AWS Bedrock / OpenAI, FastAPI, Streamlit) integrating SQL text-to-query generation, vendor contract risk assessment, guardrails-enforced policies, and automated purchase approval workflows.

### Critical Gaps
1. **Local / Third-Party Vector Database:** Relies on local ChromaDB or Pinecone rather than utilizing Google Cloud's managed **Vertex AI Vector Search (ScaNN)**.
2. **Missing A2A Protocol Implementation:** Agent handoffs are tightly coupled inside LangGraph nodes rather than exposing independent A2A Agent Cards for distributed enterprise invocation.
3. **Model Armor Sensitive Data Protection (SDP):** Vendor contract uploads and purchase order prompts are processed without automated PII/PCI redaction.

---

### Actionable Implementation Steps

#### 1. Migrate Vector Index to Vertex AI Vector Search
Replace local Chroma embeddings with Google Cloud Vertex AI Vector Search ScaNN endpoints:
```python
from google.cloud import aiplatform

aiplatform.init(project="procurement-prod", location="us-central1")
index_endpoint = aiplatform.MatchingEngineIndexEndpoint("projects/.../indexEndpoints/123456789")

response = index_endpoint.find_neighbors(
    deployed_index_id="procurement_contracts_v1",
    queries=[contract_embedding],
    num_neighbors=5
)
```

#### 2. Provide a Parallel Google ADK Runner
Alongside the existing LangGraph graph, provide an ADK runner (`src/adk_runner.py`) using Google's Agent Development Kit:
```python
from google.genai.agent import Agent, Runner

procurement_agent = Agent(
    name="ProcurementIntelligenceAgent",
    model="gemini-2.0-flash",
    instructions="You are an enterprise procurement copilot...",
    tools=[query_vendor_catalog, audit_contract_risk]
)
```

#### 3. Integrate Model Armor for Purchase Approvals
Configure Model Armor to inspect all PO generation requests and block prompt injections or unapproved vendor bank routing modifications.
