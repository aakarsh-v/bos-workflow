import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState
from utils.config import get_config


def b03(state: AgentState):
    """Return partial state with BO3 results (no in-place mutation)."""
    metrics = state.get("raw_metrics", {})
    outstanding = metrics.get("outstanding", {})
    perf = metrics.get("performance", {})

    config = get_config()
    bo_conf = next((b for b in config.get("business_objectives", []) if b["bo_code"] == "BO3"), {})

    last_month_ar = outstanding.get("last_month_ar", 100000)
    sales_mtd = perf.get("mtd_sales_value", 0)
    last_month_sales = perf.get("last_month_sales", 1) or 1

    target_ar_benchmark = last_month_ar * (sales_mtd / last_month_sales)
    actual_ar = outstanding.get("outstanding_amount", 0)

    if actual_ar > 0:
        ratio_quantum = target_ar_benchmark / actual_ar
    else:
        ratio_quantum = 2.0

    ratio_quantum = max(0.5, min(ratio_quantum, 1.5))
    ratio_ageing = outstanding.get("ageing_index", 1.0)
    final_ratio = ratio_quantum * ratio_ageing

    return {"bo_results": {"BO3": {"ratio": final_ratio, "quantum_ratio": ratio_quantum}}}