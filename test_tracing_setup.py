#!/usr/bin/env python
"""Quick test script to verify LangSmith tracing configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

print("=== LangSmith Tracing Configuration ===")
print(f"Tracing Enabled: {os.getenv('LANGCHAIN_TRACING_V2')}")
print(f"API Key: {'SET' if os.getenv('LANGCHAIN_API_KEY') else 'NOT SET'}")
print(f"Project: {os.getenv('LANGCHAIN_PROJECT', 'NOT SET')}")
print(f"Endpoint: {os.getenv('LANGCHAIN_ENDPOINT', 'default')}")
print()

tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1", "yes")
api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")

if tracing_enabled and api_key:
    print("[OK] LangSmith tracing is properly configured!")
    print(f"  Traces will appear in project: {os.getenv('LANGCHAIN_PROJECT', 'bos-workflow')}")
    print("  Run 'python main.py' to generate traces.")
else:
    print("[WARNING] LangSmith tracing is NOT properly configured.")
    if not tracing_enabled:
        print("  - Set LANGCHAIN_TRACING_V2=true in .env")
    if not api_key:
        print("  - Set LANGCHAIN_API_KEY in .env")

