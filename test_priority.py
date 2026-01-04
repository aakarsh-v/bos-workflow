from nodes.resolve_priority import prioritize
from utils.config import get_config

def run_test():
    cfg = get_config()
    print("Loaded explicit order:", cfg.get("priority_overrides", {}).get("explicit_order"))

    # All ratios set low so all grades become 'D'
    state = {
        "agent_id": "1",
        "date": "2024-01-01",
        "raw_metrics": {},
        "bo_results": {
            "BO1": {"ratio": 0.0},
            "BO2": {"ratio": 0.0},
            "BO3": {"ratio": 0.0},
            "BO4": {"ratio": 0.0},
            "BO5": {"ratio": 0.0}
        },
        "final_priority_order": []
    }

    result = prioritize(state)
    print("Final priority order:", result.get("final_priority_order"))

if __name__ == "__main__":
    run_test()
