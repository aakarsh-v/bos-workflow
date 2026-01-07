# LangSmith Tracing Setup

## Overview

LangSmith tracing is configured for this workflow. Traces will appear in your LangSmith dashboard when you run the **main workflow** (`main.py`).

## Important Notes

### Mock Workflows Don't Generate Traces

The mock workflows (`run_workflow_mock.py` and `mock_parallel_runner.py`) **do NOT use LangGraph**, so they will **NOT generate LangSmith traces**. They are standalone scripts that call node functions directly.

**To generate traces, you must run:**
```powershell
python main.py
```

### Environment Variables

Your `.env` file should contain:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key_here
LANGCHAIN_PROJECT=bos-workflow-tracing
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

## How to Verify Tracing is Working

1. **Check environment variables are loaded:**
   ```powershell
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Tracing:', os.getenv('LANGCHAIN_TRACING_V2')); print('API Key:', 'SET' if os.getenv('LANGCHAIN_API_KEY') else 'NOT SET')"
   ```

2. **Run the main workflow:**
   ```powershell
   python main.py
   ```
   You should see: `✓ LangSmith tracing enabled for project: bos-workflow-tracing`

3. **Check LangSmith Dashboard:**
   - Go to https://smith.langchain.com
   - Navigate to the "bos-workflow-tracing" project
   - You should see traces for each workflow run

## Troubleshooting

### Traces Not Appearing?

1. **Verify .env file exists and has correct values**
   - File should be in the project root
   - Values should be set (quotes are optional)

2. **Ensure you're running main.py, not the mock workflows**
   - Mock workflows don't use LangGraph, so no traces

3. **Check API key is valid**
   - Verify the key works at https://smith.langchain.com

4. **Check project name**
   - Traces go to the project specified in `LANGCHAIN_PROJECT`
   - Default is "bos-workflow-tracing"

5. **Verify environment variables are loaded before LangGraph imports**
   - `load_dotenv()` must be called before importing `langgraph`
   - This is already done in `main.py`

## What Gets Traced?

When running `main.py`, LangGraph automatically traces:
- Each node execution (fetch, b01, b02, b03, b04, b05, merge_bo_results, prioritize)
- State transitions
- Workflow execution flow
- Timing information

