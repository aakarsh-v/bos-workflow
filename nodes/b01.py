import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState


def b01(state: AgentState):
    metrics = state.get("raw_metrics", {})
    perf = metrics.get("performance", {})

    # BO1: PRIVATE LABEL SALES
    # Ratio = Actual MTD / Expected Baseline
    ratio = perf.get("mtd_sales_value", 0) / 40.0

    state.setdefault("bo_results", {})["BO1"] = {"ratio": ratio}
    return state
