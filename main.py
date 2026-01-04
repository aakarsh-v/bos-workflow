from langgraph.graph import StateGraph, END
from state import AgentState
from nodes.fetch_data import fetch_data
from nodes.calculate_scores import calculate_scores
from nodes.resolve_priority import prioritize

workflow = StateGraph(AgentState)

workflow.add_node("fetch", fetch_data)
workflow.add_node("calculate", calculate_scores)
workflow.add_node("prioritize", prioritize)

workflow.set_entry_point("fetch")
workflow.add_edge("fetch", "calculate")
workflow.add_edge("calculate", "prioritize")
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