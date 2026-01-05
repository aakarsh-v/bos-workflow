import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState


def b03(state: AgentState):
    metrics = state.get("raw_metrics", {})
    outstanding = metrics.get("outstanding", {})

    # BO3: AR / OUTSTANDING CONTROL
    ratio = outstanding.get("outstanding_amount", 0) / 100000.0

    state.setdefault("bo_results", {})["BO3"] = {"ratio": ratio}
    return state
