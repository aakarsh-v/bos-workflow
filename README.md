# Business Objective Workflow

A LangGraph-based workflow system for calculating and prioritizing business objectives (BOs) for sales agents. This workflow fetches agent performance data, calculates scores for different business objectives, and determines priority order based on grading rules.

## Overview

The workflow consists of three main stages:

1. **Fetch Data**: Retrieves agent performance metrics from a FastAPI backend
2. **Calculate Scores**: Computes ratios and scores for each business objective
3. **Prioritize**: Assigns grades and determines final priority order

## Prerequisites

- Python 3.8 or higher
- FastAPI backend running on `http://localhost:8000` (or modify the base URL in `nodes/fetch_data.py`)

## Installation

1. Clone or navigate to this repository:
   ```bash
   cd biz_objective_workflow
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

```
biz_objective_workflow/
├── main.py                 # Main workflow definition and entry point
├── state.py                # AgentState TypedDict definition
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── nodes/
│   ├── fetch_data.py      # Fetches data from FastAPI endpoints
│   ├── calculate_scores.py # Calculates BO ratios and scores
│   └── resolve_priority.py # Assigns grades and prioritizes BOs
└── utils/
    ├── config.py          # Configuration (currently empty)
    └── helpers.py         # Helper functions (currently empty)
```

## Usage

### Running the Workflow

1. **Ensure the FastAPI backend is running** on `http://localhost:8000` (or `http://127.0.0.1:8000`)

   **Required API Endpoints** (verified available at `/docs`):
   - ✅ `GET /api/salesagentperformancesummary/` - Returns array with `ff_agent_id` and `mtd_sales_value` fields
   - ✅ `GET /api/retaileroutstandingsummary/` - Returns array with `outstanding_amount` field
   - ✅ `GET /api/ffagentnewretaileronboardingsummary/` - Returns onboarding data
   - ✅ `GET /api/ffagentdcactivitysummary/` - Returns DC activity data

   You can verify all endpoints are available by visiting `http://127.0.0.1:8000/docs` in your browser.

2. **Run the workflow (production / full graph)**:
   ```powershell
   python main.py
   ```

   Note: `main.py` currently uses an in-memory checkpointer (`MemorySaver`) for development. To persist state to a SQLite file instead, edit `main.py` and replace the in-memory saver with `SqliteSaver.from_conn_string("bos_state.db")`.

3. **Run the sequential mock runner (quick local run, with optional JSON snapshot)**:
   ```powershell
   python run_workflow_mock.py --thread-id session_1 --persist-path .\mock_state_session_1.json
   ```

4. **Run the parallel mock runner (simulates concurrent BO nodes, with optional JSON snapshot)**:
   ```powershell
   python mock_parallel_runner.py --thread-id session_1 --persist-path .\mock_parallel_state_session_1.json
   ```

5. **Enable tracing integrations (optional)**

   To enable LangSmith tracing (or other tracing integrations), set the API key in your environment or `.env` file:
   ```powershell
   $Env:LANGSMITH_API_KEY = "your_langsmith_key_here"
   ```
   The runners and `main.py` check for `LANGSMITH_API_KEY` and will log its presence; configure the tracing SDK as needed for your environment.

### Using the Workflow Programmatically

```python
from main import app

# Initialize state
initial_state = {
    "agent_id": "123",
    "date": "2024-01-01",
    "raw_metrics": {},
    "bo_results": {},
    "final_priority_order": []
}

# Execute workflow
result = app.invoke(initial_state)

# Access results
print(f"Priority Order: {result['final_priority_order']}")
print(f"BO Results: {result['bo_results']}")
```

## Workflow Details

### 1. Fetch Data Node (`fetch_data`)

- Fetches performance metrics from FastAPI endpoints
- Filters data by `agent_id` and `date`
- Stores results in `state["raw_metrics"]`

**Required API Response Format:**
- `salesagentperformancesummary/`: List with `ff_agent_id` and `mtd_sales_value` fields
- `retaileroutstandingsummary/`: List with `outstanding_amount` field
- `ffagentdcactivitysummary/`: List with activity data

### 2. Calculate Scores Node (`calculate_scores`)

Calculates ratios for all 5 business objectives:

- **BO1**: PRIVATE LABEL SALES
  - Formula: `mtd_sales_value / 40.0` (baseline)
  
- **BO2**: DC CHECK-INS (Coverage × Effort)
  - Factor A - Coverage: `unique_dcs_visited / total_dcs`
  - Factor B - Effort: `check_ins_count / expected_check_ins`
  - Composite Score: `Coverage × Effort`
  
- **BO3**: AR / OUTSTANDING CONTROL
  - Formula: `outstanding_amount / 100000.0` (baseline)
  
- **BO4**: OVERALL SALES (Velocity × Spread)
  - Velocity: `mtd_sales_value / active_days_mtd`
  - Spread: `mtd_order_count / last12m_order_count` (normalized)
  - Composite Score: `Velocity × Spread / 1000.0`
  
- **BO5**: MARKET DEVELOPMENT (Enablement + Expansion)
  - Enablement: `new_retailers_mtd / new_retailers_last_month`
  - Expansion: `new_retailers_mtd / new_retailers_last12m`
  - Composite Score: `(Enablement + Expansion) / 2.0`

### 3. Prioritize Node (`prioritize`)

- **Grading System**:
  - Grade A: ratio >= 1.0
  - Grade B: 0.5 <= ratio < 1.0
  - Grade C: 0.25 <= ratio < 0.5
  - Grade D: ratio < 0.25

- **Conditional Rules**:
  - If BO3 (AR Control) is Grade D, then BO4 (Sales) is capped at Grade B

- **Default Priority Order**: `["BO1", "BO2", "BO4", "BO3", "BO5"]`
- **Sorting Logic**: Objectives are sorted first by grade (D, C, B, A - lower grades get higher priority), then by default order

## State Structure

The workflow uses an `AgentState` TypedDict with the following fields:

```python
{
    "agent_id": str,              # Agent identifier
    "date": str,                  # Date for filtering data
    "raw_metrics": Dict[str, Any], # Fetched API data
    "bo_results": Dict[str, Dict], # Calculated ratios and grades per BO
    "final_priority_order": List[str] # Final prioritized list of BOs
}
```

## Troubleshooting

### Common Issues

1. **ConnectionError or requests.exceptions.ConnectionError**
   - **Solution**: Ensure the FastAPI backend is running on `http://localhost:8000`
   - Check the base URL in `nodes/fetch_data.py` if your backend runs on a different port

2. **KeyError when accessing API response fields**
   - **Solution**: Verify that your API endpoints return the expected data structure
   - Check that `ff_agent_id`, `mtd_sales_value`, and `outstanding_amount` fields exist

3. **StopIteration error in fetch_data**
   - **Solution**: Ensure the API returns data matching the provided `agent_id`
   - The code uses `next()` which will fail if no matching agent is found

4. **Import errors**
   - **Solution**: Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're running Python 3.8+

### Modifying the Backend URL

To use a different backend URL, edit `nodes/fetch_data.py`:

```python
base_url = "http://your-backend-url:port/api"
```

## Dependencies

- `langgraph`: Workflow orchestration framework
- `requests`: HTTP library for API calls

See `requirements.txt` for specific versions.

## Development

### Adding New Business Objectives

1. Add calculation logic in `nodes/calculate_scores.py`
2. Update grading/prioritization rules in `nodes/resolve_priority.py`
3. Update the default priority order if needed

### Extending the Workflow

To add new nodes:

1. Create a new function in the `nodes/` directory
2. Import and add it to the workflow in `main.py`:
   ```python
   workflow.add_node("node_name", node_function)
   workflow.add_edge("previous_node", "node_name")
   ```

## Notes

- The workflow expects the FastAPI backend to be running and accessible
- Some filtering logic is simplified (e.g., using `outstanding[0]` instead of proper agent mapping)
- The `onboarding` data is fetched but not currently used in calculations
- Error handling can be enhanced for production use


