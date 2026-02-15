-- =====================================================
-- EXAM TELEMETRY SYSTEM - DATABASE MIGRATION
-- =====================================================
-- This migration transforms the flat error logging system
-- into a comprehensive exam performance tracking platform
--
-- EXECUTION ORDER:
-- 1. Create study_sessions table
-- 2. Create mock_exams table
-- 3. Alter errors table to add session_id FK
-- 4. Create indexes for performance
-- =====================================================

-- =====================================================
-- TABLE 1: STUDY SESSIONS (Micro-Performance Tracking)
-- =====================================================
-- Tracks individual study blocks (e.g., "20 Math questions in 40 minutes")
-- Enables speed/accuracy correlation analysis

CREATE TABLE IF NOT EXISTS public.study_sessions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User Association
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Temporal Data
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Exam Context
    exam_type TEXT NOT NULL CHECK (
        exam_type IN ('FUVEST', 'ENEM', 'UNICAMP', 'ITA/IME', 'SAT', 'General')
    ),
    subject TEXT NOT NULL,

    -- Performance Metrics
    total_questions INTEGER NOT NULL CHECK (total_questions > 0),
    correct_count INTEGER NOT NULL DEFAULT 0 CHECK (correct_count >= 0),
    duration_minutes NUMERIC(6,2) NOT NULL CHECK (duration_minutes > 0),

    -- Computed Fields (stored for query performance)
    accuracy_percentage NUMERIC(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_questions > 0 THEN (correct_count::numeric / total_questions::numeric) * 100
            ELSE 0
        END
    ) STORED,

    pace_per_question NUMERIC(6,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_questions > 0 THEN duration_minutes / total_questions
            ELSE 0
        END
    ) STORED,

    -- Constraints
    CONSTRAINT valid_correct_count CHECK (correct_count <= total_questions)
);

-- Row Level Security (RLS) for study_sessions
ALTER TABLE public.study_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own sessions"
    ON public.study_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions"
    ON public.study_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sessions"
    ON public.study_sessions FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own sessions"
    ON public.study_sessions FOR DELETE
    USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX idx_study_sessions_user_date ON public.study_sessions(user_id, date DESC);
CREATE INDEX idx_study_sessions_exam_type ON public.study_sessions(exam_type);
CREATE INDEX idx_study_sessions_subject ON public.study_sessions(subject);

-- =====================================================
-- TABLE 2: MOCK EXAMS (Macro-Performance Tracking)
-- =====================================================
-- Tracks full simulated exam scores
-- Enables trajectory analysis (score evolution over time)

CREATE TABLE IF NOT EXISTS public.mock_exams (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User Association
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Exam Identification
    exam_name TEXT NOT NULL,  -- e.g., "FUVEST 2024 Phase 1", "SAT Practice Test 8"
    exam_type TEXT NOT NULL CHECK (
        exam_type IN ('FUVEST', 'ENEM', 'UNICAMP', 'ITA/IME', 'SAT', 'General')
    ),

    -- Temporal Data
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Scoring
    total_score NUMERIC(10,2) NOT NULL CHECK (total_score >= 0),
    max_possible_score NUMERIC(10,2) NOT NULL CHECK (max_possible_score > 0),

    -- Computed Percentage
    score_percentage NUMERIC(5,2) GENERATED ALWAYS AS (
        (total_score / max_possible_score) * 100
    ) STORED,

    -- Optional Section Breakdown (JSONB for flexibility)
    -- Example: {"Math": 780, "Reading": 720, "Writing": 650}
    breakdown_json JSONB DEFAULT '{}'::jsonb,

    -- Optional Notes
    notes TEXT,

    -- Constraints
    CONSTRAINT valid_score CHECK (total_score <= max_possible_score)
);

-- Row Level Security (RLS) for mock_exams
ALTER TABLE public.mock_exams ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own mock exams"
    ON public.mock_exams FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own mock exams"
    ON public.mock_exams FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own mock exams"
    ON public.mock_exams FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own mock exams"
    ON public.mock_exams FOR DELETE
    USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX idx_mock_exams_user_date ON public.mock_exams(user_id, date DESC);
CREATE INDEX idx_mock_exams_exam_type ON public.mock_exams(exam_type);
CREATE INDEX idx_mock_exams_exam_name ON public.mock_exams(exam_name);

-- =====================================================
-- TABLE 3: ERRORS TABLE MODIFICATION
-- =====================================================
-- Add foreign key to link errors to study sessions
-- This allows contextual error analysis

ALTER TABLE public.errors
ADD COLUMN IF NOT EXISTS session_id UUID REFERENCES public.study_sessions(id) ON DELETE SET NULL;

-- Add exam_type to errors for better filtering
ALTER TABLE public.errors
ADD COLUMN IF NOT EXISTS exam_type TEXT DEFAULT 'General' CHECK (
    exam_type IN ('FUVEST', 'ENEM', 'UNICAMP', 'ITA/IME', 'SAT', 'General')
);

-- Index for session-based queries
CREATE INDEX IF NOT EXISTS idx_errors_session ON public.errors(session_id);
CREATE INDEX IF NOT EXISTS idx_errors_exam_type ON public.errors(exam_type);

-- =====================================================
-- FUNCTION: Update timestamp trigger
-- =====================================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-updating updated_at
CREATE TRIGGER update_study_sessions_updated_at
    BEFORE UPDATE ON public.study_sessions
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_mock_exams_updated_at
    BEFORE UPDATE ON public.mock_exams
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- =====================================================
-- VIEWS FOR ANALYTICS (Optional - for complex queries)
-- =====================================================

-- View: Session Performance Summary
CREATE OR REPLACE VIEW public.v_session_performance AS
SELECT
    s.id,
    s.user_id,
    s.date,
    s.exam_type,
    s.subject,
    s.total_questions,
    s.correct_count,
    s.duration_minutes,
    s.accuracy_percentage,
    s.pace_per_question,
    COUNT(e.id) AS error_count,
    -- Speed Zone Classification
    CASE
        WHEN s.pace_per_question < 1.5 THEN 'Rushing'
        WHEN s.pace_per_question >= 1.5 AND s.pace_per_question <= 3.0 THEN 'Optimal'
        ELSE 'Slow'
    END AS pace_zone,
    -- Accuracy Classification
    CASE
        WHEN s.accuracy_percentage >= 80 THEN 'Mastery'
        WHEN s.accuracy_percentage >= 60 THEN 'Developing'
        ELSE 'Struggling'
    END AS accuracy_zone
FROM public.study_sessions s
LEFT JOIN public.errors e ON e.session_id = s.id
GROUP BY s.id;

-- View: Mock Exam Trajectory
CREATE OR REPLACE VIEW public.v_mock_exam_trajectory AS
SELECT
    user_id,
    exam_type,
    exam_name,
    date,
    total_score,
    max_possible_score,
    score_percentage,
    ROW_NUMBER() OVER (PARTITION BY user_id, exam_type ORDER BY date) AS attempt_number,
    LAG(score_percentage) OVER (PARTITION BY user_id, exam_type ORDER BY date) AS previous_score,
    score_percentage - LAG(score_percentage) OVER (PARTITION BY user_id, exam_type ORDER BY date) AS improvement
FROM public.mock_exams
ORDER BY user_id, exam_type, date;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Next Steps:
-- 1. Run this SQL in Supabase SQL Editor
-- 2. Verify tables created: study_sessions, mock_exams
-- 3. Verify errors table has new columns: session_id, exam_type
-- 4. Test RLS policies work correctly
-- =====================================================
