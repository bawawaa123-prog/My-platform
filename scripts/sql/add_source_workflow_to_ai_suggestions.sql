-- ============================================================
-- Migration: add_source_workflow_to_ai_suggestions
-- 
-- Adds source_workflow column to ai_suggestions table.
-- This field distinguishes Single-Agent RAG suggestions
-- from Multi-Agent workflow suggestions.
-- ============================================================

-- MySQL version
ALTER TABLE ai_suggestions
  ADD COLUMN source_workflow VARCHAR(50) NOT NULL DEFAULT 'single_agent'
  COMMENT 'Origin of the suggestion: single_agent or multi_agent';

-- ============================================================
-- SQLite version (if applicable)
-- ============================================================
-- ALTER TABLE ai_suggestions ADD COLUMN source_workflow TEXT NOT NULL DEFAULT 'single_agent';
