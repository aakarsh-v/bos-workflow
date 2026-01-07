# BOS Workflow Setup Guide

## Overview

This guide covers setting up both **Execution Tracing** (LangSmith) and **Execution Persistence** (PostgreSQL) for the BOS workflow.

## 1️⃣ Execution Tracing with LangSmith

### Purpose
Track what ran, in what order, how long it took, and what failed.

### Requirements
- **Account**: AIarm account on LangSmith
- **Project Name**: `bos-workflow-aiarm` (or custom)
- **Scope**: Nodes, edges, retries, errors
- **Unit**: A single workflow run

### Setup Steps

1. **Get AIarm LangSmith API Key**
   - Log into LangSmith with AIarm account
   - Navigate to Settings → API Keys
   - Create or copy API key

2. **Configure Environment Variables**
   
   Copy `env.template` to `.env`:
   ```bash
   cp env.template .env
   ```
   
   Update `.env` with AIarm credentials:
   ```env
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   LANGCHAIN_API_KEY=your_aiarm_langsmith_api_key_here
   LANGCHAIN_PROJECT=bos-workflow-aiarm
   ```

3. **Verify Setup**
   ```bash
   python test_tracing_setup.py
   ```
   
   Should show: `[OK] LangSmith tracing is properly configured!`

4. **Run Workflow**
   ```bash
   python main.py
   ```
   
   Traces will appear in LangSmith dashboard under project: `bos-workflow-aiarm`

### What Gets Traced
- Each node execution (fetch, b01, b02, b03, b04, b05, merge_bo_results, prioritize)
- State transitions between nodes
- Edge traversals
- Execution timing
- Errors and retries
- Full workflow execution flow

## 2️⃣ Execution Persistence with PostgreSQL

### Purpose
Store workflow state at each step for resume, replay, and debugging.

### Requirements
- **Tool**: LangGraph persistence / checkpointer
- **Scope**: Serialized state snapshots
- **Purpose**: Resume, replay, debug
- **Store**: PostgreSQL database

### Setup Steps

1. **Install PostgreSQL**
   - Install PostgreSQL 12+ on your system
   - Ensure PostgreSQL service is running

2. **Create Database**
   ```sql
   CREATE DATABASE bos_workflow_db;
   ```

3. **Run Schema Migration**
   ```bash
   psql -U postgres -d bos_workflow_db -f database/schema.sql
   ```
   
   Or using psql:
   ```sql
   \i database/schema.sql
   ```

4. **Configure Environment Variables**
   
   Update `.env` with Postgres connection details:
   ```env
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=bos_workflow_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_postgres_password_here
   POSTGRES_CONNECTION_STRING=postgresql://postgres:your_password@localhost:5432/bos_workflow_db
   ```

5. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   This installs:
   - `langgraph-checkpoint-postgres`
   - `psycopg2-binary`

6. **Verify Setup**
   ```bash
   python main.py
   ```
   
   Should show: `[OK] Postgres persistence enabled: bos_workflow_db`

### Schema Overview

The schema includes three main tables:

1. **`checkpoints`**: Stores workflow state snapshots
   - `thread_id`: Groups checkpoints from same workflow run
   - `checkpoint_state`: Full AgentState JSON
   - `metadata`: Additional checkpoint info

2. **`checkpoint_blobs`**: Optional large binary data

3. **`workflow_runs`**: High-level workflow metadata
   - `thread_id`: Unique workflow run identifier
   - `agent_id`: Agent being processed
   - `status`: Execution status
   - `final_priority_order`: Final result

See `database/README.md` for full schema documentation.

### Using Persistence

#### Resume Workflow
```python
from main import app

# Get state from previous run
config = {"configurable": {"thread_id": "session_1"}}
snapshot = app.get_state(config)

# Resume from checkpoint
result = app.invoke(None, config=config)
```

#### Query State History
```sql
-- Get all checkpoints for a workflow run
SELECT checkpoint_id, checkpoint_ns, created_at, checkpoint_state
FROM checkpoints
WHERE thread_id = 'session_1'
ORDER BY created_at;

-- Get latest checkpoint
SELECT * FROM latest_checkpoints WHERE thread_id = 'session_1';
```

## Verification Checklist

### Tracing
- [ ] AIarm LangSmith API key configured
- [ ] Project name set to `bos-workflow-aiarm`
- [ ] `test_tracing_setup.py` shows OK
- [ ] Traces appear in LangSmith dashboard after running `main.py`

### Persistence
- [ ] PostgreSQL installed and running
- [ ] Database `bos_workflow_db` created
- [ ] Schema migration executed successfully
- [ ] Postgres connection string configured in `.env`
- [ ] `main.py` shows `[OK] Postgres persistence enabled`
- [ ] Can query checkpoints from database

## Troubleshooting

### Tracing Not Working
1. Verify API key is correct (AIarm account)
2. Check project name matches in dashboard
3. Ensure env vars loaded before LangGraph imports
4. Check LangSmith dashboard for errors

### Persistence Not Working
1. Verify PostgreSQL is running: `pg_isready`
2. Check connection string format
3. Verify database exists: `psql -l`
4. Check schema was created: `\dt` in psql
5. Test connection: `psql -U postgres -d bos_workflow_db`

### Common Errors

**"Postgres persistence not available"**
- Install: `pip install langgraph-checkpoint-postgres psycopg2-binary`
- Check connection string in `.env`

**"relation does not exist"**
- Run schema migration: `psql -d bos_workflow_db -f database/schema.sql`

**"authentication failed"**
- Verify POSTGRES_USER and POSTGRES_PASSWORD in `.env`

## Next Steps

1. **Schema Approval**: Review `database/schema.sql` and get approval from database team
2. **Production Setup**: Configure production Postgres instance
3. **Monitoring**: Set up monitoring for tracing and persistence
4. **Backup Strategy**: Plan for checkpoint data backup/archival

## Support

- Schema Documentation: `database/README.md`
- Tracing Documentation: `TRACING_SETUP.md`
- Environment Template: `env.template`

