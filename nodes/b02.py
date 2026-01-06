import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState
from utils.config import get_config


def b02(state: AgentState):
    """Return partial state with BO2 results (no in-place mutation)."""
    metrics = state.get("raw_metrics", {})
    dc_data = metrics.get("dc_activity", {})

    config = get_config()
    bo_conf = next((b for b in config.get("business_objectives", []) if b["bo_code"] == "BO2"), {})
    factors = {f["factor_code"]: f for f in bo_conf.get("factors", [])}

    f_cov_conf = factors.get("B2A", {}).get("benchmark", {})
    multiplier_cov = f_cov_conf.get("multiplier", 1.5)

    last_month_unique = dc_data.get("last_month_unique_dcs", 20)
    total_portfolio = dc_data.get("total_dcs", 1)

    benchmark_cov = min(last_month_unique * multiplier_cov, total_portfolio)
    actual_cov = dc_data.get("unique_dcs_visited", 0)
    ratio_cov = min(actual_cov / benchmark_cov, 1.5) if benchmark_cov > 0 else 0

    f_eff_conf = factors.get("B2B", {}).get("benchmark", {})
    multiplier_eff = f_eff_conf.get("multiplier", 1.25)

    last_month_total = dc_data.get("last_month_checkins", 40)
    benchmark_eff = last_month_total * multiplier_eff
    actual_eff = dc_data.get("check_ins_count", 0)
    ratio_eff = min(actual_eff / benchmark_eff, 1.5) if benchmark_eff > 0 else 0

    final_ratio = ratio_cov * ratio_eff

    return {"bo_results": {"BO2": {"ratio": final_ratio, "coverage_ratio": ratio_cov, "effort_ratio": ratio_eff}}}