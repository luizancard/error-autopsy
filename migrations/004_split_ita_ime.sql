-- =====================================================
-- MIGRATION 004: Split ITA/IME into separate exam types
-- =====================================================
-- Updates CHECK constraints on all tables to allow
-- 'ITA' and 'IME' as separate exam types instead of 'ITA/IME'.
-- Also migrates existing 'ITA/IME' data to 'ITA'.
-- =====================================================

-- 1. Update existing data from 'ITA/IME' to 'ITA'
UPDATE public.mock_exams SET exam_type = 'ITA' WHERE exam_type = 'ITA/IME';
UPDATE public.study_sessions SET exam_type = 'ITA' WHERE exam_type = 'ITA/IME';
UPDATE public.errors SET exam_type = 'ITA' WHERE exam_type = 'ITA/IME';

-- 2. Drop old CHECK constraints
ALTER TABLE public.mock_exams DROP CONSTRAINT IF EXISTS mock_exams_exam_type_check;
ALTER TABLE public.study_sessions DROP CONSTRAINT IF EXISTS study_sessions_exam_type_check;
ALTER TABLE public.errors DROP CONSTRAINT IF EXISTS errors_exam_type_check;

-- 3. Add new CHECK constraints with 'ITA' and 'IME' separated
ALTER TABLE public.mock_exams ADD CONSTRAINT mock_exams_exam_type_check
    CHECK (exam_type IN ('FUVEST', 'ENEM', 'UNICAMP', 'ITA', 'IME', 'SAT', 'General'));

ALTER TABLE public.study_sessions ADD CONSTRAINT study_sessions_exam_type_check
    CHECK (exam_type IN ('FUVEST', 'ENEM', 'UNICAMP', 'ITA', 'IME', 'SAT', 'General'));

ALTER TABLE public.errors ADD CONSTRAINT errors_exam_type_check
    CHECK (exam_type IN ('FUVEST', 'ENEM', 'UNICAMP', 'ITA', 'IME', 'SAT', 'General'));

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Run this in Supabase SQL Editor
-- Existing 'ITA/IME' records are migrated to 'ITA'
-- =====================================================
