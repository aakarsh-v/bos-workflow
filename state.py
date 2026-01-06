import operator
from typing import TypedDict, List, Dict, Any, Annotated

def merge_dicts(a: Dict, b: Dict) -> Dict:
    """Merges two dictionaries. Used to combine results from parallel BO nodes."""
    return {**a, **b}

class AgentState(TypedDict):
    agent_id: str
    date: str
    raw_metrics: Dict[str, Any]
    
    # FIX: Use Annotated with merge_dicts so parallel nodes add to this dict 
    # instead of overwriting each other.
    bo_results: Annotated[Dict[str, Dict], merge_dicts]
    
    final_priority_order: List[str]