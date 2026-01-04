import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState

def fetch_data(state: AgentState):
    base_url = "http://localhost:8000/api"
    
    # Fetching from the provided routes
    performance = requests.get(f"{base_url}/salesagentperformancesummary/").json()
    outstanding = requests.get(f"{base_url}/retaileroutstandingsummary/").json()
    onboarding = requests.get(f"{base_url}/ffagentnewretaileronboardingsummary/").json()
    dc_activity = requests.get(f"{base_url}/ffagentdcactivitysummary/").json()

    # Filter for specific agent (Mock filtering logic)
    agent_id_int = int(state['agent_id'])
    state["raw_metrics"] = {
        "performance": next(x for x in performance if x['ff_agent_id'] == agent_id_int),
        "outstanding": outstanding[0] if outstanding else {}, # Based on retailer_id/agent mapping
        "dc_activity": dc_activity[0] if dc_activity else {},
        "onboarding": next((x for x in onboarding if x.get('ff_agent_id') == agent_id_int), {}) if onboarding else {}
    }
    return state