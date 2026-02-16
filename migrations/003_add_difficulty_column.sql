-- Migration 003: Add difficulty column to errors table
-- Adds difficulty level tracking for error analysis

ALTER TABLE errors
ADD COLUMN IF NOT EXISTS difficulty TEXT DEFAULT 'Medium' CHECK (
    difficulty IN ('Easy', 'Medium', 'Hard')
);

CREATE INDEX IF NOT EXISTS idx_errors_difficulty ON errors(difficulty);
