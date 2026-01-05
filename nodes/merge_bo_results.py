import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState


def merge_bo_results(state: AgentState):
    # Join point / synchronization node. Ensures bo_results exists and returns state.
    state.setdefault("bo_results", {})
    return state
