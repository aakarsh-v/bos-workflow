import os
from dotenv import load_dotenv

# 1. Load Environment variables FIRST (before any LangGraph imports)
# This is critical for LangSmith tracing to work
load_dotenv()

# Verify tracing is enabled
tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1", "yes")
api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
project = os.getenv("LANGCHAIN_PROJECT", "bos-workflow")

if tracing_enabled and api_key:
    print(f"[OK] LangSmith tracing enabled for project: {project}")
else:
    print("[WARNING] LangSmith tracing not enabled. Set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY in .env")

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver  # Use in-memory saver for now

from state import AgentState
from nodes.fetch_data import fetch_data
from nodes.resolve_priority import prioritize

# New BO nodes
from nodes.b01 import b01
from nodes.b02 import b02
from nodes.b03 import b03
from nodes.b04 import b04
from nodes.b05 import b05
from nodes.merge_bo_results import merge_bo_results

# 2. Setup Persistence
# Use in-memory persistence for development/testing. Switch to SqliteSaver
# when you want durable DB-backed persistence.
memory = MemorySaver()

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("fetch", fetch_data)
workflow.add_node("b01", b01)
workflow.add_node("b02", b02)
workflow.add_node("b03", b03)
workflow.add_node("b04", b04)
workflow.add_node("b05", b05)
workflow.add_node("merge_bo_results", merge_bo_results)
workflow.add_node("prioritize", prioritize)

# Define Edges
workflow.set_entry_point("fetch")

workflow.add_edge("fetch", "b01")
workflow.add_edge("fetch", "b02")
workflow.add_edge("fetch", "b03")
workflow.add_edge("fetch", "b04")
workflow.add_edge("fetch", "b05")

workflow.add_edge("b01", "merge_bo_results")
workflow.add_edge("b02", "merge_bo_results")
workflow.add_edge("b03", "merge_bo_results")
workflow.add_edge("b04", "merge_bo_results")
workflow.add_edge("b05", "merge_bo_results")

workflow.add_edge("merge_bo_results", "prioritize")
workflow.add_edge("prioritize", END)

# 3. Compile with Checkpointer
# This enables the "persistence" requirement
app = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    # Example usage with Persistence
    initial_state = {
        "agent_id": "123",
        "date": "2024-01-01",
        "raw_metrics": {},
        "bo_results": {},
        "final_priority_order": []
    }
    
    # 4. Use a thread_id config
    # This ID tracks the specific workflow session in the database
    config = {"configurable": {"thread_id": "session_1"}}

    try:
        print("Starting persistent workflow...")
        # LangGraph automatically sends traces to LangSmith when env vars are set
        # Traces will appear in the project specified by LANGCHAIN_PROJECT
        # invoke now takes the config argument
        result = app.invoke(initial_state, config=config)
        
        print("Workflow executed successfully!")
        print(f"Final priority order: {result.get('final_priority_order', [])}")
        print(f"BO Results: {result.get('bo_results', {})}")
        
        # Verify Persistence: You can now query the state later using:
        # snapshot = app.get_state(config)
        # print("Saved State Snapshot:", snapshot.values)

    except Exception as e:
        print(f"Error running workflow: {e}")
        print("\nNote: Make sure the FastAPI backend is running on http://localhost:8000")
        raise