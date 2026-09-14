-- ============================================================================
-- Text Analysis Management System - SQLite Database Schema
-- ============================================================================
-- This file contains the essential database schema for SQLite
-- Optimized for single-file EXE packaging
-- ============================================================================

-- Enable foreign keys (SQLite requires explicit enabling)
PRAGMA foreign_keys = ON;

-- ============================================================================
-- TABLE: sources
-- Description: Information sources (news, social media, blogs, etc.)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    link_sources TEXT NOT NULL,
    importance REAL NOT NULL DEFAULT 0.0 CHECK (importance >= 0.0 AND importance <= 1.0),
    country TEXT NOT NULL,
    city TEXT NULL,
    description TEXT NULL,
    accounts TEXT NULL,
    note TEXT NULL,
    ownership TEXT NULL,
    date_entry TIMESTAMP NULL,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_importance_range CHECK (importance >= 0.0 AND importance <= 1.0)
);

-- Indexes for sources table
CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_name_unique ON sources (name);
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources (type);
CREATE INDEX IF NOT EXISTS idx_sources_importance ON sources (importance DESC);
CREATE INDEX IF NOT EXISTS idx_sources_date_creation ON sources (date_creation DESC);
CREATE INDEX IF NOT EXISTS idx_sources_country ON sources (country);

-- ============================================================================
-- TABLE: contents
-- Description: Content data linked to sources
-- ============================================================================
CREATE TABLE IF NOT EXISTS contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_data TEXT NOT NULL,
    attachments TEXT NULL,
    note TEXT NULL,
    importance REAL NOT NULL DEFAULT 0.0 CHECK (importance >= 0.0 AND importance <= 1.0),
    date_content TIMESTAMP NULL,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    sources_id INTEGER NOT NULL,
    FOREIGN KEY (sources_id) REFERENCES sources(id) ON DELETE CASCADE,
    CONSTRAINT chk_contents_importance_range CHECK (importance >= 0.0 AND importance <= 1.0)
);

-- Indexes for contents table
CREATE INDEX IF NOT EXISTS idx_contents_sources_id ON contents (sources_id);
CREATE INDEX IF NOT EXISTS idx_contents_date_content ON contents (date_content DESC);
CREATE INDEX IF NOT EXISTS idx_contents_importance ON contents (importance DESC);
CREATE INDEX IF NOT EXISTS idx_contents_date_creation ON contents (date_creation DESC);

-- ============================================================================
-- TABLE: content_analysis
-- Description: Analysis and classification of content
-- ============================================================================
CREATE TABLE IF NOT EXISTS content_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    list_names_people TEXT NULL,
    list_names_places TEXT NULL,
    coordinates TEXT NULL,
    classification TEXT NULL,
    list_sides TEXT NULL,
    date_analysis TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE
);

-- Indexes for content_analysis table
CREATE INDEX IF NOT EXISTS idx_content_analysis_content_id ON content_analysis (content_id);
CREATE INDEX IF NOT EXISTS idx_content_analysis_classification ON content_analysis (classification);
CREATE INDEX IF NOT EXISTS idx_content_analysis_date_analysis ON content_analysis (date_analysis DESC);

-- ============================================================================
-- TRIGGERS
-- Description: Automatic triggers for timestamps (SQLite syntax)
-- ============================================================================

-- Apply triggers to sources table
DROP TRIGGER IF EXISTS trigger_sources_update_timestamp;
CREATE TRIGGER trigger_sources_update_timestamp
    AFTER UPDATE ON sources
    FOR EACH ROW
    WHEN NEW.date_modified = OLD.date_modified
BEGIN
    UPDATE sources SET date_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Apply triggers to contents table
DROP TRIGGER IF EXISTS trigger_contents_update_timestamp;
CREATE TRIGGER trigger_contents_update_timestamp
    AFTER UPDATE ON contents
    FOR EACH ROW
    WHEN NEW.date_modified = OLD.date_modified
BEGIN
    UPDATE contents SET date_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Apply triggers to content_analysis table
DROP TRIGGER IF EXISTS trigger_content_analysis_update_timestamp;
CREATE TRIGGER trigger_content_analysis_update_timestamp
    AFTER UPDATE ON content_analysis
    FOR EACH ROW
    WHEN NEW.date_modified = OLD.date_modified
BEGIN
    UPDATE content_analysis SET date_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
