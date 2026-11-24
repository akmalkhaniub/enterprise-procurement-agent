import json
import operator
import os
from typing import Annotated, Any, Sequence, TypedDict

import requests
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VALID_ROUTES = ("DataAnalyst", "Researcher", "OpsEngineer", "FINISH")
MAX_SUPERVISOR_TURNS = 8

_llm = None
_collection = None
_collection_initialized = False
_sql_agent_executor = None
_research_agent_executor = None
_ops_agent_executor = None
_graph = None

# Expose `collection` attribute for monkeypatching in offline tests.
collection = None


def get_llm():
    """Lazily initialize ChatVertexAI so pure-routing and mock-vector tests run offline."""
    global _llm
    if _llm is None:
        from langchain_google_vertexai import ChatVertexAI

        model_name = os.getenv("MODEL_NAME", "gemini-3.8-flash")
        _llm = ChatVertexAI(model_name=model_name, temperature=0)
    return _llm


def get_collection():
    """Lazily initialize ChromaDB collection if not already set or mocked."""
    global _collection, _collection_initialized, collection
    if collection is not None:
        return collection
    if not _collection_initialized:
        _collection_initialized = True
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            chroma_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))
            emb_fn = embedding_functions.DefaultEmbeddingFunction()
            _collection = chroma_client.get_collection("vendor_contracts", embedding_function=emb_fn)
            collection = _collection
        except Exception:
            _collection = None
    return collection


def get_sql_agent_executor():
    global _sql_agent_executor
    if _sql_agent_executor is None:
        from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
        from langchain_community.utilities.sql_database import SQLDatabase
        from langgraph.prebuilt import create_react_agent

        llm = get_llm()
        db_path = os.path.join(BASE_DIR, "procurement.db")
        db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        _sql_agent_executor = create_react_agent(
            llm,
            sql_toolkit.get_tools(),
            prompt=(
                "You are an expert Data Analyst specializing in SaaS procurement data. "
                "You have access to a SQL database with 'vendors', 'contracts', and "
                "'purchase_orders' tables. Write and execute SQL to answer the user's "
                "question accurately."
            ),
        )
    return _sql_agent_executor


@tool
def search_vendor_policies(query: str) -> str:
    """Searches the vector database for vendor contracts, policies, and compliance documents."""
    active_collection = collection if collection is not None else get_collection()
    if not active_collection:
        return "Vector database not initialized."
    results = active_collection.query(query_texts=[query], n_results=3)

    if not results.get("documents") or not results["documents"][0]:
        return "No relevant documents found."

    docs = results["documents"][0]
    return "\n\n".join(docs)


def get_research_agent_executor():
    global _research_agent_executor
    if _research_agent_executor is None:
        from langgraph.prebuilt import create_react_agent

        _research_agent_executor = create_react_agent(
            get_llm(),
            [search_vendor_policies],
            prompt=(
                "You are a Procurement Policy Researcher. You have access to a vector "
                "database containing vendor contracts, SLAs, and security policies. "
                "Use the search tool to find relevant information."
            ),
        )
    return _research_agent_executor


@tool
def call_ops_tool(server_name: str, tool_name: str, arguments: str) -> str:
    """Calls an MCP tool on the Ops Gateway.
    Args:
        server_name: The name of the server (e.g., 'devops', 'mlops', 'agentops', 'dbops', 'github', 'secrets').
        tool_name: The name of the tool to call.
        arguments: A JSON string of arguments to pass to the tool.
    """
    gateway_url = os.environ.get("OPS_GATEWAY_URL", "http://localhost:8080")
    url = f"{gateway_url}/{server_name}/call/{tool_name}"

    try:
        args_dict = json.loads(arguments) if arguments else {}
        response = requests.post(url, json=args_dict, timeout=30)
        if response.status_code == 404:
            return f"Error: Tool or server not found. {response.text}"
        response.raise_for_status()
        data = response.json()
        return str(data.get("result", data))
    except Exception as e:
        return f"Error calling ops tool: {e}"


def get_ops_agent_executor():
    global _ops_agent_executor
    if _ops_agent_executor is None:
        from langgraph.prebuilt import create_react_agent

        _ops_agent_executor = create_react_agent(
            get_llm(),
            [call_ops_tool],
            prompt=(
                "You are an expert Platform & Ops Engineer. You have access to a suite "
                "of MCP tools across DevOps, MLOps, AgentOps, DBOps, GitHub, and Secrets "
                "Management. Use the 'call_ops_tool' function to execute these tools. "
                "You must provide arguments as a valid JSON string."
            ),
        )
    return _ops_agent_executor


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str


supervisor_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are the Procurement Supervisor Agent. Your job is to route the user's request to the correct subagent.\n"
        "Available subagents:\n"
        "1. 'DataAnalyst': For querying the SQL database about purchase orders, vendors, pricing, or contract values.\n"
        "2. 'Researcher': For querying vendor SLAs, security policies, and contract terms from the document knowledge base.\n"
        "3. 'OpsEngineer': For infrastructure operations, vector DB provisioning, github operations, secret management, AWS access, and platform tasks.\n"
        "If the request requires multiple, you can route to one first, then another. If the task is fully answered, output 'FINISH'.\n\n"
        "Respond ONLY with one of these exact words: 'DataAnalyst', 'Researcher', 'OpsEngineer', or 'FINISH'.",
    ),
    MessagesPlaceholder(variable_name="messages"),
])


def parse_supervisor_route(raw_text: str, messages: Sequence[BaseMessage]) -> str:
    """Deterministically resolve the next subagent route with loop & turn-budget guards."""
    if len(messages) >= MAX_SUPERVISOR_TURNS:
        return "FINISH"

    tokens = raw_text.strip().split() if raw_text and raw_text.strip() else []
    cleaned = tokens[0].strip("'\"`.,:;!") if len(tokens) == 1 else ""
    if cleaned in VALID_ROUTES:
        candidate = cleaned
    else:
        # Check last occurrence in text rather than fixed if/elif priority
        last_pos = -1
        candidate = "FINISH"
        text = raw_text or ""
        for route in VALID_ROUTES:
            pos = text.rfind(route)
            if pos > last_pos:
                last_pos = pos
                candidate = route

    # Stagnation guard: if the most recent AIMessage already came from `candidate`, finish
    if messages and isinstance(messages[-1], AIMessage) and getattr(messages[-1], "name", None) == candidate:
        return "FINISH"

    return candidate


def extract_text(content: Any) -> str:
    if isinstance(content, list):
        text_parts = []
        for m in content:
            if isinstance(m, dict):
                if m.get("type") == "text" and "text" in m:
                    text_parts.append(m["text"])
                elif "text" in m:
                    text_parts.append(m["text"])
            elif isinstance(m, str):
                text_parts.append(m)
        return " ".join(text_parts)
    return str(content)


def supervisor_node(state: AgentState):
    messages = state["messages"]
    if len(messages) >= MAX_SUPERVISOR_TURNS:
        return {"next_agent": "FINISH"}
    response = get_llm().invoke(supervisor_prompt.format_messages(messages=messages))
    next_step = parse_supervisor_route(extract_text(response.content), messages)
    return {"next_agent": next_step}


def sql_node(state: AgentState):
    result = get_sql_agent_executor().invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=extract_text(result["messages"][-1].content), name="DataAnalyst")]}


def research_node(state: AgentState):
    result = get_research_agent_executor().invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=extract_text(result["messages"][-1].content), name="Researcher")]}


def ops_node(state: AgentState):
    result = get_ops_agent_executor().invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=extract_text(result["messages"][-1].content), name="OpsEngineer")]}


def build_graph():
    global _graph
    if _graph is None:
        from langgraph.graph import END, START, StateGraph

        workflow = StateGraph(AgentState)
        workflow.add_node("Supervisor", supervisor_node)
        workflow.add_node("DataAnalyst", sql_node)
        workflow.add_node("Researcher", research_node)
        workflow.add_node("OpsEngineer", ops_node)

        workflow.add_edge(START, "Supervisor")
        workflow.add_conditional_edges(
            "Supervisor",
            lambda state: state["next_agent"],
            {
                "DataAnalyst": "DataAnalyst",
                "Researcher": "Researcher",
                "OpsEngineer": "OpsEngineer",
                "FINISH": END,
            },
        )
        workflow.add_edge("DataAnalyst", "Supervisor")
        workflow.add_edge("Researcher", "Supervisor")
        workflow.add_edge("OpsEngineer", "Supervisor")
        _graph = workflow.compile()
    return _graph


def __getattr__(name: str):
    if name == "graph":
        return build_graph()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":
    if "GOOGLE_API_KEY" not in os.environ:
        print("Please set GOOGLE_API_KEY environment variable.")
    else:
        inputs = {"messages": [HumanMessage(content="How much did we spend on TechCorp Inc.?")]}
        for output in build_graph().stream(inputs, stream_mode="updates"):
            for key, value in output.items():
                print(f"Output from node '{key}':")
                print("---")
                if "messages" in value:
                    print(value["messages"][-1].content)
                else:
                    print(value)
                print("\n")
