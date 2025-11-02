-- =============================================
-- CodeGuard AI - PostgreSQL Database Schema
-- Version: 1.0.0
-- Created: 2025-11-02
-- Database: PostgreSQL 15+ (Supabase)
-- =============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for encryption functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================
-- ENUMS
-- =============================================

CREATE TYPE user_role AS ENUM ('DEVELOPER', 'ADMIN');
CREATE TYPE review_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');
CREATE TYPE finding_severity AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW');
CREATE TYPE ai_model AS ENUM ('GEMINI_FLASH', 'VERTEX_AI_PRO');
CREATE TYPE export_format AS ENUM ('JSON', 'PDF');

-- =============================================
-- TABLE: users
-- =============================================

CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,  -- Clerk user_id
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    avatar_url VARCHAR(500),
    role user_role DEFAULT 'DEVELOPER' NOT NULL,
    daily_analysis_count INTEGER DEFAULT 0 NOT NULL,
    last_analysis_date DATE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT check_daily_count CHECK (daily_analysis_count >= 0)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_quota ON users(last_analysis_date, daily_analysis_count);

COMMENT ON TABLE users IS 'Central user management linked to Clerk OAuth';
COMMENT ON COLUMN users.id IS 'Clerk user_id from OAuth provider';
COMMENT ON COLUMN users.role IS 'DEVELOPER has basic access, ADMIN has full config access';

-- =============================================
-- TABLE: code_reviews (Aggregate Root)
-- =============================================

CREATE TABLE code_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    code_content BYTEA NOT NULL,  -- Encrypted with AES-256-GCM
    quality_score INTEGER,
    status review_status DEFAULT 'PENDING' NOT NULL,
    total_findings INTEGER DEFAULT 0 NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP,
    
    CONSTRAINT check_quality_score CHECK (quality_score >= 0 AND quality_score <= 100),
    CONSTRAINT check_total_findings CHECK (total_findings >= 0),
    CONSTRAINT check_completed_at CHECK (
        (status = 'COMPLETED' AND completed_at IS NOT NULL) OR
        (status != 'COMPLETED' AND completed_at IS NULL)
    )
);

CREATE INDEX idx_reviews_user_id ON code_reviews(user_id);
CREATE INDEX idx_reviews_status ON code_reviews(status);
CREATE INDEX idx_reviews_created_desc ON code_reviews(created_at DESC);
CREATE INDEX idx_reviews_user_status ON code_reviews(user_id, status);
CREATE INDEX idx_reviews_user_created ON code_reviews(user_id, created_at DESC);

COMMENT ON TABLE code_reviews IS 'Main analysis sessions with encrypted code storage';
COMMENT ON COLUMN code_reviews.code_content IS 'Encrypted using pgcrypto with AES-256-GCM';
COMMENT ON COLUMN code_reviews.quality_score IS 'Calculated: max(0, 100 - sum(penalties))';

-- =============================================
-- TABLE: agent_findings
-- =============================================

CREATE TABLE agent_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    review_id UUID NOT NULL REFERENCES code_reviews(id) ON DELETE CASCADE,
    agent_type VARCHAR(100) NOT NULL,
    severity finding_severity NOT NULL,
    issue_type VARCHAR(200) NOT NULL,
    line_number INTEGER NOT NULL,
    code_snippet TEXT,
    message TEXT NOT NULL,
    suggestion TEXT,
    metrics JSONB,
    ai_explanation JSONB,  -- Sprint 3: Gemini-generated
    mcp_references TEXT[],  -- Sprint 3: MCP server references
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT check_line_number CHECK (line_number > 0),
    CONSTRAINT check_ai_explanation_structure CHECK (
        ai_explanation IS NULL OR (
            ai_explanation ? 'explanation' AND
            ai_explanation ? 'model_used' AND
            ai_explanation ? 'generated_at'
        )
    )
);

CREATE INDEX idx_findings_review_id ON agent_findings(review_id);
CREATE INDEX idx_findings_severity ON agent_findings(severity);
CREATE INDEX idx_findings_agent_type ON agent_findings(agent_type);
CREATE INDEX idx_findings_line_number ON agent_findings(line_number);
CREATE INDEX idx_findings_review_severity ON agent_findings(review_id, severity);
CREATE INDEX idx_findings_review_agent ON agent_findings(review_id, agent_type);

COMMENT ON TABLE agent_findings IS 'Individual vulnerability/issue findings from agents';
COMMENT ON COLUMN agent_findings.ai_explanation IS 'Sprint 3: JSON with {explanation, attack_example, fix_code, cwe_ref, owasp_category}';
COMMENT ON COLUMN agent_findings.mcp_references IS 'Sprint 3: References to OWASP/CVE/Custom KB MCP servers';

-- =============================================
-- TABLE: agent_configs (Sprint 4)
-- =============================================

CREATE TABLE agent_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(100) UNIQUE NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_by VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT check_config_structure CHECK (
        jsonb_typeof(config_json) = 'object'
    )
);

CREATE INDEX idx_configs_agent_type ON agent_configs(agent_type);
CREATE INDEX idx_configs_enabled ON agent_configs(is_enabled);

COMMENT ON TABLE agent_configs IS 'Configuration per agent (thresholds, rules, enable/disable)';
COMMENT ON COLUMN agent_configs.config_json IS 'Example: {"complexity_threshold": 10, "enable_ai": true, "custom_rules": [...]}';

-- =============================================
-- TABLE: ai_config (Sprint 3)
-- =============================================

CREATE TABLE ai_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ai_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    model_type ai_model DEFAULT 'GEMINI_FLASH' NOT NULL,
    rate_limit_daily INTEGER DEFAULT 100 NOT NULL,
    budget_threshold_usd DECIMAL(10, 2) DEFAULT 150.00 NOT NULL,
    current_spend_usd DECIMAL(10, 6) DEFAULT 0.00 NOT NULL,
    updated_by VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT check_rate_limit CHECK (rate_limit_daily > 0),
    CONSTRAINT check_budget CHECK (budget_threshold_usd > 0 AND current_spend_usd >= 0)
);

CREATE INDEX idx_ai_config_enabled ON ai_config(ai_enabled);

COMMENT ON TABLE ai_config IS 'Global AI settings (single row table)';
COMMENT ON COLUMN ai_config.model_type IS 'GEMINI_FLASH for dev, VERTEX_AI_PRO for production';

-- =============================================
-- TABLE: ai_usage_metrics (Sprint 3)
-- =============================================

CREATE TABLE ai_usage_metrics (
    id BIGSERIAL PRIMARY KEY,
    review_id UUID REFERENCES code_reviews(id) ON DELETE CASCADE,
    model_used VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    latency_ms INTEGER NOT NULL,
    cache_hit BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT check_tokens CHECK (
        prompt_tokens >= 0 AND
        completion_tokens >= 0 AND
        total_tokens = prompt_tokens + completion_tokens
    ),
    CONSTRAINT check_cost CHECK (cost_usd >= 0),
    CONSTRAINT check_latency CHECK (latency_ms >= 0)
);

CREATE INDEX idx_metrics_review_id ON ai_usage_metrics(review_id);
CREATE INDEX idx_metrics_created_desc ON ai_usage_metrics(created_at DESC);
CREATE INDEX idx_metrics_model ON ai_usage_metrics(model_used);
CREATE INDEX idx_metrics_cache_hit ON ai_usage_metrics(cache_hit);
CREATE INDEX idx_metrics_created_model ON ai_usage_metrics(created_at, model_used);

COMMENT ON TABLE ai_usage_metrics IS 'AI API usage tracking for cost analysis';
COMMENT ON COLUMN ai_usage_metrics.cache_hit IS 'TRUE if explanation retrieved from Redis cache';

-- =============================================
-- TABLE: mcp_context_logs (Sprint 3)
-- =============================================

CREATE TABLE mcp_context_logs (
    id BIGSERIAL PRIMARY KEY,
    finding_id UUID REFERENCES agent_findings(id) ON DELETE CASCADE,
    mcp_server VARCHAR(100) NOT NULL,
    query TEXT NOT NULL,
    response JSONB,
    latency_ms INTEGER NOT NULL,
    success BOOLEAN DEFAULT TRUE NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT check_mcp_latency CHECK (latency_ms >= 0),
    CONSTRAINT check_error_message CHECK (
        (success = FALSE AND error_message IS NOT NULL) OR
        (success = TRUE AND error_message IS NULL)
    )
);

CREATE INDEX idx_mcp_finding_id ON mcp_context_logs(finding_id);
CREATE INDEX idx_mcp_server ON mcp_context_logs(mcp_server);
CREATE INDEX idx_mcp_created ON mcp_context_logs(created_at DESC);
CREATE INDEX idx_mcp_success ON mcp_context_logs(success);
CREATE INDEX idx_mcp_server_success ON mcp_context_logs(mcp_server, success);

COMMENT ON TABLE mcp_context_logs IS 'Model Context Protocol server query logs';
COMMENT ON COLUMN mcp_context_logs.mcp_server IS 'owasp-mcp, cve-mcp, custom-kb-mcp';

-- =============================================
-- TABLE: event_logs
-- =============================================

CREATE TABLE event_logs (
    id BIGSERIAL PRIMARY KEY,
    review_id UUID REFERENCES code_reviews(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    agent_name VARCHAR(100),
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_events_review_id ON event_logs(review_id);
CREATE INDEX idx_events_type ON event_logs(event_type);
CREATE INDEX idx_events_created_desc ON event_logs(created_at DESC);
CREATE INDEX idx_events_review_type ON event_logs(review_id, event_type);

COMMENT ON TABLE event_logs IS 'Analysis event timeline for progress tracking';
COMMENT ON COLUMN event_logs.event_type IS 'ANALYSIS_STARTED, AGENT_COMPLETED, ANALYSIS_COMPLETED, ANALYSIS_FAILED, CONFIG_UPDATED';

-- =============================================
-- TABLE: analysis_export_logs
-- =============================================

CREATE TABLE analysis_export_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    review_id UUID NOT NULL REFERENCES code_reviews(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    export_format export_format NOT NULL,
    file_path VARCHAR(500),
    file_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT check_file_size CHECK (file_size_bytes >= 0)
);

CREATE INDEX idx_exports_user_id ON analysis_export_logs(user_id);
CREATE INDEX idx_exports_review_id ON analysis_export_logs(review_id);
CREATE INDEX idx_exports_created_desc ON analysis_export_logs(created_at DESC);

COMMENT ON TABLE analysis_export_logs IS 'Export audit trail for compliance';

-- =============================================
-- TRIGGERS
-- =============================================

-- Update updated_at timestamp on users table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_configs_updated_at BEFORE UPDATE ON agent_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_config_updated_at BEFORE UPDATE ON ai_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- FUNCTIONS
-- =============================================

-- Function to calculate quality score
CREATE OR REPLACE FUNCTION calculate_quality_score(p_review_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_score INTEGER;
BEGIN
    SELECT 100 - SUM(
        CASE severity
            WHEN 'CRITICAL' THEN 10
            WHEN 'HIGH' THEN 5
            WHEN 'MEDIUM' THEN 2
            WHEN 'LOW' THEN 1
            ELSE 0
        END
    )
    INTO v_score
    FROM agent_findings
    WHERE review_id = p_review_id;
    
    RETURN GREATEST(COALESCE(v_score, 100), 0);
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- INITIAL DATA
-- =============================================

-- Insert default agent configurations
INSERT INTO agent_configs (agent_type, is_enabled, config_json) VALUES
('SecurityAgent', TRUE, '{"timeout_seconds": 30, "enable_ai": true, "rules": ["detect_eval", "detect_sql_injection", "detect_hardcoded_credentials"]}'::jsonb),
('QualityAgent', TRUE, '{"complexity_threshold": 10, "duplication_threshold": 0.20, "function_length_threshold": 100}'::jsonb),
('PerformanceAgent', TRUE, '{"nested_loop_threshold": 3, "detect_expensive_operations": true}'::jsonb),
('StyleAgent', TRUE, '{"check_pep8": true, "check_docstrings": true, "line_length_limit": 88}'::jsonb)
ON CONFLICT (agent_type) DO NOTHING;

-- Insert default AI configuration
INSERT INTO ai_config (ai_enabled, model_type, rate_limit_daily, budget_threshold_usd) VALUES
(TRUE, 'GEMINI_FLASH', 100, 150.00)
ON CONFLICT DO NOTHING;

-- =============================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================

-- Enable RLS on sensitive tables
ALTER TABLE code_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_export_logs ENABLE ROW LEVEL SECURITY;

-- Users can only see their own code reviews
CREATE POLICY users_own_reviews ON code_reviews
    FOR ALL
    USING (auth.uid()::VARCHAR = user_id);

-- Users can only see findings for their own reviews
CREATE POLICY users_own_findings ON agent_findings
    FOR SELECT
    USING (review_id IN (SELECT id FROM code_reviews WHERE user_id = auth.uid()::VARCHAR));

-- Users can only see their own export logs
CREATE POLICY users_own_exports ON analysis_export_logs
    FOR ALL
    USING (auth.uid()::VARCHAR = user_id);

-- Admins can see all data
CREATE POLICY admins_all_reviews ON code_reviews
    FOR ALL
    USING (EXISTS (SELECT 1 FROM users WHERE id = auth.uid()::VARCHAR AND role = 'ADMIN'));

-- =============================================
-- GRANTS
-- =============================================

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE ON users TO authenticated;
GRANT SELECT, INSERT, UPDATE ON code_reviews TO authenticated;
GRANT SELECT, INSERT ON agent_findings TO authenticated;
GRANT SELECT, INSERT ON ai_usage_metrics TO authenticated;
GRANT SELECT, INSERT ON mcp_context_logs TO authenticated;
GRANT SELECT, INSERT ON event_logs TO authenticated;
GRANT SELECT, INSERT ON analysis_export_logs TO authenticated;

-- Grant read-only access to config tables for developers
GRANT SELECT ON agent_configs TO authenticated;
GRANT SELECT ON ai_config TO authenticated;

-- Grant full access to config tables for admins (handled by RLS policies)
