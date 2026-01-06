import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState


def _find_for_agent(items, agent_identifiers, agent_id):
    if not items:
        return {}
    for it in items:
        for key in agent_identifiers:
            if key in it and str(it.get(key)) == str(agent_id):
                return it
    return items[0] if items else {}


def fetch_data(state: AgentState):
    base_url = "http://127.0.0.1:8000/api"

    # New API endpoints discovered in /docs
    perf_list = requests.get(f"{base_url}/sebo4overallsalesperformancedaily/").json()
    dc_perf_list = requests.get(f"{base_url}/sebo2dccheckinsperformancedaily/").json()
    dc_baseline_list = requests.get(f"{base_url}/sebo2dccheckinsbaselinemonthly/").json()
    ar_list = requests.get(f"{base_url}/sebo3arcontrolperformancedaily/").json()
    pl_perf_list = requests.get(f"{base_url}/sebo1plperformancedaily/").json()

    agent_id = state.get('agent_id')

    # Try common identifier keys used by the API: 'se_id' or 'ff_agent_id'
    perf = _find_for_agent(perf_list, ['se_id', 'ff_agent_id', 'agent_id'], agent_id)
    dc_perf = _find_for_agent(dc_perf_list, ['se_id', 'ff_agent_id', 'agent_id'], agent_id)
    dc_base = _find_for_agent(dc_baseline_list, ['se_id', 'ff_agent_id', 'agent_id'], agent_id)
    ar = _find_for_agent(ar_list, ['se_id', 'ff_agent_id', 'agent_id'], agent_id)
    pl_perf = _find_for_agent(pl_perf_list, ['se_id', 'ff_agent_id', 'agent_id'], agent_id)

    # Map API fields into the existing internal raw_metrics shape expected by nodes
    performance = {
        # prefer 'sales_mtd' from overall sales, fallback to PL 'pl_unique_cart_orders_mtd'
        'mtd_sales_value': perf.get('sales_mtd') or pl_perf.get('pl_unique_cart_orders_mtd', 0),
        # active days may not be provided by API; default to 1 to avoid division by zero
        'active_days_mtd': perf.get('active_days_mtd', 1),
        # use unique_transacting_dcs_mtd as proxy for order count if available
        'mtd_order_count': perf.get('unique_transacting_dcs_mtd', 0),
        # last12m placeholder if not present
        'last12m_order_count': perf.get('last12m_order_count', 1)
    }

    dc_activity = {
        'unique_dcs_visited': dc_perf.get('unique_dcs_checked_in_mtd', 0),
        'total_dcs': dc_base.get('total_dcs_in_portfolio', dc_base.get('total_dcs', 0)),
        'check_ins_count': dc_perf.get('total_checkins_mtd', 0),
        'expected_check_ins': dc_base.get('effort_benchmark_checkins', 1)
    }

    outstanding = {
        # Map net_ar_today to outstanding amount (best-effort based on schema)
        'outstanding_amount': ar.get('net_ar_today', ar.get('ar_composite_score', 0))
    }

    # Onboarding/new retailers endpoint not present explicitly; try to derive from PL perf or default
    onboarding = {
        'new_retailers_mtd': pl_perf.get('pl_unique_cart_orders_mtd', 0),
        'new_retailers_last_month': 1,
        'new_retailers_last12m': 1
    }

    state['raw_metrics'] = {
        'performance': performance,
        'dc_activity': dc_activity,
        'outstanding': outstanding,
        'onboarding': onboarding
    }

    return state