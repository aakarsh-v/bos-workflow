import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState
from utils.config import get_config

def b01(state: AgentState):
    metrics = state.get("raw_metrics", {})
    perf = metrics.get("performance", {})
    
    # Load Config
    config = get_config()
    bo_conf = next((b for b in config.get("business_objectives", []) if b["bo_code"] == "BO1"), {})
    
    # 1. Get Benchmark Parameters
    bench_conf = bo_conf.get("benchmark", {})
    growth_multiplier = bench_conf.get("growth_multiplier", 2.0)
    
    # 2. Calculate Benchmark: (Last 12 Month PL Sales * Growth) / 12
    # Note: Assuming fetch_data populates 'pl_sales_last_12m', defaulting to 240 if missing for safety
    last_12m_pl = perf.get("pl_sales_last_12m", 240) 
    monthly_benchmark = (last_12m_pl * growth_multiplier) / 12.0
    
    # 3. Calculate Ratio
    actual_mtd = perf.get("mtd_sales_value", 0)
    ratio = actual_mtd / monthly_benchmark if monthly_benchmark > 0 else 0.0

    # Store result
    state.setdefault("bo_results", {})["BO1"] = {
        "ratio": ratio, 
        "actual": actual_mtd, 
        "benchmark": monthly_benchmark
    }
    return state