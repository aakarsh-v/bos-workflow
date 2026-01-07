-- PostgreSQL Schema for BOS Workflow State Persistence
-- This schema stores workflow execution state snapshots for resume, replay, and debugging
-- 
-- Schema Version: 1.0
-- Created: 2025-01-07
-- Purpose: Persist LangGraph workflow state at each step

-- Main table for storing workflow checkpoints
-- Each row represents a state snapshot at a specific point in workflow execution
CREATE TABLE IF NOT EXISTS checkpoints (
    -- Primary key: unique identifier for each checkpoint
    checkpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Thread/Session identifier: groups checkpoints from the same workflow run
    thread_id VARCHAR(255) NOT NULL,
    
    -- Checkpoint sequence number: order of checkpoints within a thread
    checkpoint_ns VARCHAR(255) NOT NULL DEFAULT '',
    
    -- Parent checkpoint reference: for checkpoint lineage/tree structure
    parent_checkpoint_id UUID REFERENCES checkpoints(checkpoint_id) ON DELETE CASCADE,
    
    -- Workflow state: serialized JSON of AgentState at this checkpoint
    -- Stores: agent_id, date, raw_metrics, bo_results, final_priority_order
    checkpoint_state JSONB NOT NULL,
    
    -- Metadata: additional information about the checkpoint
    -- Can store: node name, edge info, error details, etc.
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for efficient querying
    CONSTRAINT checkpoints_thread_ns_unique UNIQUE (thread_id, checkpoint_ns)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_parent_id ON checkpoints(parent_checkpoint_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at);
CREATE INDEX IF NOT EXISTS idx_checkpoints_state_agent_id ON checkpoints USING GIN ((checkpoint_state->>'agent_id'));

-- Table for storing checkpoint blobs (for large state objects if needed)
CREATE TABLE IF NOT EXISTS checkpoint_blobs (
    blob_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checkpoint_id UUID NOT NULL REFERENCES checkpoints(checkpoint_id) ON DELETE CASCADE,
    blob_data BYTEA,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_checkpoint_blobs_checkpoint_id ON checkpoint_blobs(checkpoint_id);

-- Table for storing workflow execution metadata
-- Tracks high-level information about workflow runs
CREATE TABLE IF NOT EXISTS workflow_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id VARCHAR(255) NOT NULL UNIQUE,
    
    -- Workflow identification
    agent_id VARCHAR(255),
    workflow_date DATE,
    
    -- Execution status
    status VARCHAR(50) DEFAULT 'running', -- running, completed, failed, cancelled
    error_message TEXT,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Final state summary (for quick access without loading full checkpoint)
    final_priority_order JSONB,
    bo_results_summary JSONB,
    
    -- Foreign key to latest checkpoint
    latest_checkpoint_id UUID REFERENCES checkpoints(checkpoint_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_thread_id ON workflow_runs(thread_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_agent_id ON workflow_runs(agent_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_started_at ON workflow_runs(started_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_checkpoints_updated_at BEFORE UPDATE ON checkpoints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for easy querying of latest checkpoint per thread
CREATE OR REPLACE VIEW latest_checkpoints AS
SELECT DISTINCT ON (thread_id)
    checkpoint_id,
    thread_id,
    checkpoint_ns,
    checkpoint_state,
    metadata,
    created_at
FROM checkpoints
ORDER BY thread_id, created_at DESC;

-- Comments for documentation
COMMENT ON TABLE checkpoints IS 'Stores workflow state snapshots at each execution step for resume/replay/debugging';
COMMENT ON TABLE checkpoint_blobs IS 'Stores large binary data associated with checkpoints if needed';
COMMENT ON TABLE workflow_runs IS 'Tracks high-level metadata about workflow executions';
COMMENT ON COLUMN checkpoints.checkpoint_state IS 'Serialized AgentState: agent_id, date, raw_metrics, bo_results, final_priority_order';
COMMENT ON COLUMN checkpoints.metadata IS 'Additional checkpoint metadata: node name, edge info, errors, etc.';
COMMENT ON COLUMN workflow_runs.final_priority_order IS 'Final BO priority order for quick access';
COMMENT ON COLUMN workflow_runs.bo_results_summary IS 'Summary of BO results (ratios, grades) for quick access';

