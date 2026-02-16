-- Migration 002: Add mock_exam_id to errors table
-- Links individual errors to the mock exam they originated from

ALTER TABLE errors
ADD COLUMN IF NOT EXISTS mock_exam_id UUID REFERENCES mock_exams(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_errors_mock_exam_id ON errors(mock_exam_id);
