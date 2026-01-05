
from langgraph.graph import StateGraph, END
from state import AgentState
from nodes.fetch_data import fetch_data
from nodes.resolve_priority import prioritize

# New BO nodes (parallelizable)
from nodes.b01 import b01
from nodes.b02 import b02
from nodes.b03 import b03
from nodes.b04 import b04
from nodes.b05 import b05
from nodes.merge_bo_results import merge_bo_results


workflow = StateGraph(AgentState)

workflow.add_node("fetch", fetch_data)
workflow.add_node("b01", b01)
workflow.add_node("b02", b02)
workflow.add_node("b03", b03)
workflow.add_node("b04", b04)
workflow.add_node("b05", b05)
workflow.add_node("merge_bo_results", merge_bo_results)
workflow.add_node("prioritize", prioritize)

workflow.set_entry_point("fetch")
# from fetch we fan-out to all BO nodes (these can run in parallel)
workflow.add_edge("fetch", "b01")
workflow.add_edge("fetch", "b02")
workflow.add_edge("fetch", "b03")
workflow.add_edge("fetch", "b04")
workflow.add_edge("fetch", "b05")

# all BO nodes converge to merge, then prioritize
workflow.add_edge("b01", "merge_bo_results")
workflow.add_edge("b02", "merge_bo_results")
workflow.add_edge("b03", "merge_bo_results")
workflow.add_edge("b04", "merge_bo_results")
workflow.add_edge("b05", "merge_bo_results")

workflow.add_edge("merge_bo_results", "prioritize")
workflow.add_edge("prioritize", END)

app = workflow.compile()

if __name__ == "__main__":
    # Example usage
    initial_state = {
        "agent_id": "123",
        "date": "2024-01-01",
        "raw_metrics": {},
        "bo_results": {},
        "final_priority_order": []
    }
    
    try:
        result = app.invoke(initial_state)
        print("Workflow executed successfully!")
        print(f"Final priority order: {result.get('final_priority_order', [])}")
        print(f"BO Results: {result.get('bo_results', {})}")
    except Exception as e:
        print(f"Error running workflow: {e}")
        print("\nNote: Make sure the FastAPI backend is running on http://localhost:8000")
        raise