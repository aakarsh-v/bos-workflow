import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState

def calculate_scores(state: AgentState):
    metrics = state["raw_metrics"]
    bo_results = {}

    # BO1: PRIVATE LABEL SALES
    # Ratio = Actual MTD / Expected Baseline
    bo_results["BO1"] = {"ratio": metrics["performance"]["mtd_sales_value"] / 40.0} 

    # BO2: DC CHECK-INS (Coverage × Effort)
    # Factor A - Coverage: Number of unique DCs visited / Total DCs
    # Factor B - Effort: Number of check-ins / Expected check-ins
    # Composite Score = Coverage × Effort
    dc_data = metrics.get("dc_activity", {})
    # Assuming dc_activity has fields like unique_dcs_visited, total_dcs, check_ins_count, expected_check_ins
    coverage = dc_data.get("unique_dcs_visited", 0) / max(dc_data.get("total_dcs", 1), 1)
    effort = dc_data.get("check_ins_count", 0) / max(dc_data.get("expected_check_ins", 1), 1)
    bo_results["BO2"] = {"ratio": coverage * effort, "coverage": coverage, "effort": effort}

    # BO3: AR / OUTSTANDING CONTROL
    # Uses Ageing Index and Quantum Ratio
    outstanding = metrics.get("outstanding", {})
    bo_results["BO3"] = {"ratio": outstanding.get("outstanding_amount", 0) / 100000.0}

    # BO4: OVERALL SALES (Velocity × Spread)
    # Velocity: MTD Sales Value / Days Active
    # Spread: Number of retailers with orders / Total retailers
    perf = metrics.get("performance", {})
    active_days = max(perf.get("active_days_mtd", 1), 1)
    velocity = perf.get("mtd_sales_value", 0) / active_days
    # Assuming we need to calculate spread from order count or retailer data
    # For now, using a simplified calculation
    spread = min(perf.get("mtd_order_count", 0) / max(perf.get("last12m_order_count", 1), 1), 1.0)
    bo_results["BO4"] = {"ratio": velocity * spread / 1000.0, "velocity": velocity, "spread": spread}

    # BO5: MARKET DEVELOPMENT (Enablement + Expansion)
    # Enablement: New retailers onboarded
    # Expansion: Growth in retailer base
    onboarding = metrics.get("onboarding", {})
    new_retailers_mtd = onboarding.get("new_retailers_mtd", 0)
    new_retailers_last_month = onboarding.get("new_retailers_last_month", 0)
    enablement = new_retailers_mtd / max(new_retailers_last_month, 1)
    expansion = new_retailers_mtd / max(onboarding.get("new_retailers_last12m", 1), 1)
    bo_results["BO5"] = {"ratio": (enablement + expansion) / 2.0, "enablement": enablement, "expansion": expansion}

    state["bo_results"] = bo_results
    return state