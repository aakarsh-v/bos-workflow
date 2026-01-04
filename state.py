from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    agent_id: str
    date: str
    raw_metrics: Dict[str, Any]      # Data from FastAPI
    bo_results: Dict[str, Dict]      # Ratios and Grades per BO
    final_priority_order: List[str]  # Output: ["BO1", "BO3", ...]