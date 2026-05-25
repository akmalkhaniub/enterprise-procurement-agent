import operator
from typing import Annotated, Any, Sequence, TypedDict
import sqlite3
import chromadb
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from chromadb.utils import embedding_functions
from langchain.tools import tool
import requests
import os
import json

# Initialize LLM
llm = ChatVertexAI(model_name="gemini-2.5-flash", temperature=0)

# --- 1. SQL Data Analyst Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "procurement.db")
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
sql_tools = sql_toolkit.get_tools()

sql_agent_executor = create_react_agent(
    llm, 
    sql_tools, 
    prompt="You are an expert Data Analyst specializing in SaaS procurement data. You have access to a SQL database with 'vendors', 'contracts', and 'purchase_orders' tables. Write and execute SQL to answer the user's question accurately."
)

# --- 2. Policy Researcher (RAG) Setup ---
chroma_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))
emb_fn = embedding_functions.DefaultEmbeddingFunction()
try:
    collection = chroma_client.get_collection("vendor_contracts", embedding_function=emb_fn)
except Exception:
    collection = None

@tool
def search_vendor_policies(query: str) -> str:
    """Searches the vector database for vendor contracts, policies, and compliance documents."""
    if not collection:
        return "Vector database not initialized."
    results = collection.query(query_texts=[query], n_results=3)
    
    if not results['documents'] or not results['documents'][0]:
        return "No relevant documents found."
        
    docs = results['documents'][0]
    return "\n\n".join(docs)

research_agent_executor = create_react_agent(
    llm, 
    [search_vendor_policies], 
    prompt="You are a Procurement Policy Researcher. You have access to a vector database containing vendor contracts, SLAs, and security policies. Use the search tool to find relevant information."
)

# --- 3. Ops Engineer (MCP Gateway) Setup ---
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

ops_agent_executor = create_react_agent(
    llm,
    [call_ops_tool],
    prompt="You are an expert Platform & Ops Engineer. You have access to a suite of MCP tools across DevOps, MLOps, AgentOps, DBOps, GitHub, and Secrets Management. Use the 'call_ops_tool' function to execute these tools. You must provide arguments as a valid JSON string."
)

# --- 4. LangGraph State & Supervisor ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the Procurement Supervisor Agent. Your job is to route the user's request to the correct subagent.\n"
               "Available subagents:\n"
               "1. 'DataAnalyst': For querying the SQL database about purchase orders, vendors, pricing, or contract values.\n"
               "2. 'Researcher': For querying vendor SLAs, security policies, and contract terms from the document knowledge base.\n"
               "3. 'OpsEngineer': For infrastructure operations, vector DB provisioning, github operations, secret management, AWS access, and platform tasks.\n"
               "If the request requires multiple, you can route to one first, then another. If the task is fully answered, output 'FINISH'.\n\n"
               "Respond ONLY with one of these exact words: 'DataAnalyst', 'Researcher', 'OpsEngineer', or 'FINISH'."),
    MessagesPlaceholder(variable_name="messages"),
])

def supervisor_node(state: AgentState):
    messages = state["messages"]
    response = llm.invoke(supervisor_prompt.format_messages(messages=messages))
    # Simple routing based on output text
    next_step = response.content.strip()
    if "DataAnalyst" in next_step:
        return {"next_agent": "DataAnalyst"}
    elif "Researcher" in next_step:
        return {"next_agent": "Researcher"}
    elif "OpsEngineer" in next_step:
        return {"next_agent": "OpsEngineer"}
    else:
        return {"next_agent": "FINISH"}

def extract_text(content):
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

def sql_node(state: AgentState):
    result = sql_agent_executor.invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=extract_text(result['messages'][-1].content))]}

def research_node(state: AgentState):
    result = research_agent_executor.invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=extract_text(result['messages'][-1].content))]}

def ops_node(state: AgentState):
    result = ops_agent_executor.invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=extract_text(result['messages'][-1].content))]}

# Build the Graph
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
        "FINISH": END
    }
)
workflow.add_edge("DataAnalyst", "Supervisor")
workflow.add_edge("Researcher", "Supervisor")
workflow.add_edge("OpsEngineer", "Supervisor")

graph = workflow.compile()

if __name__ == "__main__":
    # Test the graph locally
    import os
    if "GOOGLE_API_KEY" not in os.environ:
        print("Please set GOOGLE_API_KEY environment variable.")
    else:
        inputs = {"messages": [HumanMessage(content="How much did we spend on TechCorp Inc.?")]}
        for output in graph.stream(inputs, stream_mode="updates"):
            for key, value in output.items():
                print(f"Output from node '{key}':")
                print("---")
                if "messages" in value:
                    print(value["messages"][-1].content)
                else:
                    print(value)
                print("\n")
