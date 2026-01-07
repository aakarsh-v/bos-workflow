# Database Schema for BOS Workflow Persistence

## Overview

This PostgreSQL schema provides persistent storage for LangGraph workflow execution state. It enables:
- **Resume**: Continue workflow execution from any checkpoint
- **Replay**: Re-execute workflow from a specific point
- **Debug**: Inspect state at each step of execution

## Schema Design

### Tables

#### 1. `checkpoints`
Primary table storing workflow state snapshots.

**Purpose**: Store serialized `AgentState` at each workflow step.

**Key Fields**:
- `thread_id`: Groups checkpoints from the same workflow run
- `checkpoint_ns`: Namespace/sequence identifier
- `checkpoint_state`: JSONB containing full AgentState
- `metadata`: Additional info (node name, errors, etc.)

**State Structure** (stored in `checkpoint_state`):
```json
{
  "agent_id": "123",
  "date": "2024-01-01",
  "raw_metrics": {
    "performance": {...},
    "dc_activity": {...},
    "outstanding": {...},
    "onboarding": {...}
  },
  "bo_results": {
    "BO1": {"ratio": 0.75, "grade": "B", ...},
    "BO2": {"ratio": 0.5, "grade": "C", ...},
    ...
  },
  "final_priority_order": ["BO2", "BO4", "BO1", "BO5", "BO3"]
}
```

#### 2. `checkpoint_blobs`
Optional table for large binary data associated with checkpoints.

#### 3. `workflow_runs`
High-level metadata about workflow executions.

**Purpose**: Quick access to workflow run information without loading full checkpoints.

**Key Fields**:
- `thread_id`: Unique identifier for workflow run
- `agent_id`: Agent being processed
- `status`: Execution status (running, completed, failed, cancelled)
- `final_priority_order`: Final result for quick access
- `bo_results_summary`: Summary of BO calculations

### Indexes

Optimized for common query patterns:
- Lookup by `thread_id` (most common)
- Lookup by `agent_id` (for agent-specific queries)
- Time-based queries (`created_at`, `started_at`)
- Status filtering

### Views

- `latest_checkpoints`: Easy access to most recent checkpoint per thread

## Installation

1. **Create Database**:
   ```sql
   CREATE DATABASE bos_workflow_db;
   ```

2. **Run Schema**:
   ```bash
   psql -U postgres -d bos_workflow_db -f database/schema.sql
   ```

3. **Verify**:
   ```sql
   \dt  -- List tables
   \d checkpoints  -- Describe checkpoints table
   ```

## Usage

### Connection String Format
```
postgresql://username:password@host:port/database
```

Example:
```
postgresql://postgres:mypassword@localhost:5432/bos_workflow_db
```

### Environment Variables
Set in `.env`:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bos_workflow_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_CONNECTION_STRING=postgresql://postgres:your_password@localhost:5432/bos_workflow_db
```

## Query Examples

### Get Latest Checkpoint for a Thread
```sql
SELECT * FROM latest_checkpoints WHERE thread_id = 'session_1';
```

### Get All Checkpoints for a Workflow Run
```sql
SELECT checkpoint_id, checkpoint_ns, created_at, checkpoint_state
FROM checkpoints
WHERE thread_id = 'session_1'
ORDER BY created_at;
```

### Get Workflow Run Status
```sql
SELECT thread_id, agent_id, status, started_at, completed_at, final_priority_order
FROM workflow_runs
WHERE agent_id = '123'
ORDER BY started_at DESC;
```

### Get Failed Workflows
```sql
SELECT thread_id, agent_id, error_message, started_at
FROM workflow_runs
WHERE status = 'failed'
ORDER BY started_at DESC;
```

## Schema Approval Checklist

- [x] Tables defined with appropriate data types
- [x] Primary keys and foreign keys established
- [x] Indexes for performance optimization
- [x] JSONB for flexible state storage
- [x] Timestamps for audit trail
- [x] Comments/documentation included
- [x] Migration script provided
- [ ] **Pending approval from database team**

## Migration Notes

- Schema uses `IF NOT EXISTS` for idempotent execution
- UUIDs for primary keys (better for distributed systems)
- JSONB for efficient JSON storage and querying
- Timestamps with timezone for accurate tracking
- Cascade deletes for data integrity

## Future Enhancements

- Partitioning by date for large-scale deployments
- Archival strategy for old checkpoints
- Compression for large state objects
- Read replicas for query performance

