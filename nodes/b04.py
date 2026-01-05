import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState


def b04(state: AgentState):
    metrics = state.get("raw_metrics", {})
    perf = metrics.get("performance", {})

    # BO4: OVERALL SALES (Velocity × Spread)
    active_days = max(perf.get("active_days_mtd", 1), 1)
    velocity = perf.get("mtd_sales_value", 0) / active_days
    spread = min(perf.get("mtd_order_count", 0) / max(perf.get("last12m_order_count", 1), 1), 1.0)
    ratio = velocity * spread / 1000.0

    state.setdefault("bo_results", {})["BO4"] = {"ratio": ratio, "velocity": velocity, "spread": spread}
    return state
