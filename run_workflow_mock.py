from nodes.calculate_scores import calculate_scores
from nodes.resolve_priority import prioritize

def run_mock():
    # Provide mocked metrics to avoid external API dependency
    state = {
        "agent_id": "123",
        "date": "2024-01-01",
        "raw_metrics": {
            "performance": {
                "mtd_sales_value": 30.0,
                "active_days_mtd": 10,
                "mtd_order_count": 20,
                "last12m_order_count": 200
            },
            "dc_activity": {
                "unique_dcs_visited": 5,
                "total_dcs": 20,
                "check_ins_count": 10,
                "expected_check_ins": 20
            },
            "outstanding": {
                "outstanding_amount": 50000
            },
            "onboarding": {
                "new_retailers_mtd": 2,
                "new_retailers_last_month": 4,
                "new_retailers_last12m": 20
            }
        },
        "bo_results": {},
        "final_priority_order": []
    }

    state = calculate_scores(state)
    state = prioritize(state)

    print("BO Results:")
    for bo, data in state.get("bo_results", {}).items():
        print(f"  {bo}: ratio={data.get('ratio'):.4f}, grade={data.get('grade')}")

    print("Final priority order:", state.get("final_priority_order"))

if __name__ == "__main__":
    run_mock()
