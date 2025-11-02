-- =============================================
-- CodeGuard AI - Sample Queries
-- Common database queries for the application
-- =============================================

-- =============================================
-- USER MANAGEMENT
-- =============================================

-- Get user with daily quota information
SELECT 
    id,
    email,
    name,
    role,
    daily_analysis_count,
    last_analysis_date,
    CASE 
        WHEN last_analysis_date = CURRENT_DATE THEN 10 - daily_analysis_count
        ELSE 10
    END AS remaining_quota
FROM users
WHERE id = 'user_2abc123xyz';

-- Reset daily quota for all users (scheduled job - runs at midnight)
UPDATE users
SET daily_analysis_count = 0
WHERE last_analysis_date < CURRENT_DATE;

-- Get all admins
SELECT id, email, name, created_at
FROM users
WHERE role = 'ADMIN'
ORDER BY created_at;

-- =============================================
-- CODE REVIEW QUERIES
-- =============================================

-- Get all reviews for a user with pagination
SELECT 
    id,
    filename,
    quality_score,
    status,
    total_findings,
    created_at,
    completed_at,
    EXTRACT(EPOCH FROM (completed_at - created_at)) AS duration_seconds
FROM code_reviews
WHERE user_id = 'user_2abc123xyz'
ORDER BY created_at DESC
LIMIT 10 OFFSET 0;

-- Get review details with finding counts by severity
SELECT 
    cr.id,
    cr.filename,
    cr.quality_score,
    cr.status,
    cr.total_findings,
    COUNT(CASE WHEN af.severity = 'CRITICAL' THEN 1 END) AS critical_count,
    COUNT(CASE WHEN af.severity = 'HIGH' THEN 1 END) AS high_count,
    COUNT(CASE WHEN af.severity = 'MEDIUM' THEN 1 END) AS medium_count,
    COUNT(CASE WHEN af.severity = 'LOW' THEN 1 END) AS low_count,
    cr.created_at,
    cr.completed_at
FROM code_reviews cr
LEFT JOIN agent_findings af ON cr.id = af.review_id
WHERE cr.id = '550e8400-e29b-41d4-a716-446655440000'
GROUP BY cr.id;

-- Get reviews with critical findings
SELECT 
    cr.id,
    cr.user_id,
    cr.filename,
    cr.quality_score,
    COUNT(af.id) AS critical_findings_count,
    cr.created_at
FROM code_reviews cr
INNER JOIN agent_findings af ON cr.id = af.review_id
WHERE af.severity = 'CRITICAL'
  AND cr.status = 'COMPLETED'
GROUP BY cr.id
ORDER BY critical_findings_count DESC, cr.created_at DESC
LIMIT 20;

-- Get average quality score by user
SELECT 
    u.id,
    u.email,
    u.name,
    COUNT(cr.id) AS total_analyses,
    ROUND(AVG(cr.quality_score), 2) AS avg_quality_score,
    MAX(cr.quality_score) AS best_score,
    MIN(cr.quality_score) AS worst_score
FROM users u
INNER JOIN code_reviews cr ON u.id = cr.user_id
WHERE cr.status = 'COMPLETED'
  AND cr.created_at >= NOW() - INTERVAL '30 days'
GROUP BY u.id, u.email, u.name
HAVING COUNT(cr.id) >= 3
ORDER BY avg_quality_score DESC;

-- =============================================
-- AGENT FINDINGS QUERIES
-- =============================================

-- Get all findings for a review, sorted by severity
SELECT 
    id,
    agent_type,
    severity,
    issue_type,
    line_number,
    message,
    suggestion,
    ai_explanation->>'explanation' AS ai_explanation_text,
    created_at
FROM agent_findings
WHERE review_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY 
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END,
    line_number;

-- Get most common vulnerabilities (last 30 days)
SELECT 
    issue_type,
    severity,
    COUNT(*) AS occurrence_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM agent_findings af
INNER JOIN code_reviews cr ON af.review_id = cr.id
WHERE cr.created_at >= NOW() - INTERVAL '30 days'
  AND cr.status = 'COMPLETED'
GROUP BY issue_type, severity
ORDER BY occurrence_count DESC
LIMIT 20;

-- Get findings with AI explanations (Sprint 3)
SELECT 
    af.id,
    af.agent_type,
    af.severity,
    af.issue_type,
    af.line_number,
    af.message,
    af.ai_explanation->>'explanation' AS explanation,
    af.ai_explanation->>'attack_example' AS attack_example,
    af.ai_explanation->>'fix_code' AS fix_code,
    af.ai_explanation->>'cwe_reference' AS cwe_reference,
    af.ai_explanation->>'model_used' AS model_used,
    af.ai_explanation->>'confidence_score' AS confidence_score
FROM agent_findings af
WHERE af.review_id = '550e8400-e29b-41d4-a716-446655440000'
  AND af.ai_explanation IS NOT NULL
ORDER BY af.severity, af.line_number;

-- Get agent performance metrics (average findings per agent)
SELECT 
    agent_type,
    COUNT(*) AS total_findings,
    ROUND(AVG(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) * 100, 2) AS critical_percentage,
    COUNT(DISTINCT review_id) AS reviews_analyzed
FROM agent_findings af
INNER JOIN code_reviews cr ON af.review_id = cr.id
WHERE cr.created_at >= NOW() - INTERVAL '7 days'
GROUP BY agent_type
ORDER BY total_findings DESC;

-- =============================================
-- AI USAGE & COST TRACKING (Sprint 3)
-- =============================================

-- Get AI usage summary for current month
SELECT 
    model_used,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) AS cache_hits,
    ROUND(SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cache_hit_rate,
    SUM(total_tokens) AS total_tokens_consumed,
    SUM(cost_usd) AS total_cost_usd,
    ROUND(AVG(latency_ms), 0) AS avg_latency_ms
FROM ai_usage_metrics
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY model_used
ORDER BY total_cost_usd DESC;

-- Get daily AI cost breakdown
SELECT 
    DATE(created_at) AS date,
    model_used,
    COUNT(*) AS requests,
    SUM(cost_usd) AS daily_cost_usd
FROM ai_usage_metrics
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at), model_used
ORDER BY date DESC, model_used;

-- Check if budget threshold is exceeded
SELECT 
    ac.budget_threshold_usd,
    ac.current_spend_usd,
    ac.budget_threshold_usd - ac.current_spend_usd AS remaining_budget_usd,
    CASE 
        WHEN ac.current_spend_usd >= ac.budget_threshold_usd THEN TRUE
        ELSE FALSE
    END AS budget_exceeded
FROM ai_config ac
LIMIT 1;

-- Update current AI spend (scheduled job - runs hourly)
UPDATE ai_config
SET current_spend_usd = (
    SELECT COALESCE(SUM(cost_usd), 0)
    FROM ai_usage_metrics
    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
);

-- =============================================
-- MCP CONTEXT LOGS (Sprint 3)
-- =============================================

-- Get MCP server performance metrics
SELECT 
    mcp_server,
    COUNT(*) AS total_queries,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) AS successful_queries,
    ROUND(SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate,
    ROUND(AVG(latency_ms), 0) AS avg_latency_ms,
    MAX(latency_ms) AS max_latency_ms
FROM mcp_context_logs
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY mcp_server
ORDER BY total_queries DESC;

-- Get failed MCP queries for debugging
SELECT 
    mcl.id,
    mcl.mcp_server,
    mcl.query,
    mcl.error_message,
    mcl.latency_ms,
    mcl.created_at,
    af.issue_type,
    af.severity
FROM mcp_context_logs mcl
INNER JOIN agent_findings af ON mcl.finding_id = af.id
WHERE mcl.success = FALSE
  AND mcl.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY mcl.created_at DESC
LIMIT 50;

-- =============================================
-- EVENT LOGS (Audit Trail)
-- =============================================

-- Get complete analysis timeline
SELECT 
    el.event_type,
    el.agent_name,
    el.event_data->>'findings_count' AS findings_count,
    el.event_data->>'progress_percent' AS progress_percent,
    el.event_data->>'execution_time_ms' AS execution_time_ms,
    el.created_at
FROM event_logs el
WHERE el.review_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY el.created_at;

-- Get failed analyses in last 24 hours
SELECT 
    cr.id,
    cr.user_id,
    cr.filename,
    cr.error_message,
    cr.created_at,
    u.email
FROM code_reviews cr
INNER JOIN users u ON cr.user_id = u.id
WHERE cr.status = 'FAILED'
  AND cr.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY cr.created_at DESC;

-- Get config change audit trail
SELECT 
    el.created_at,
    el.event_data->>'agent_type' AS agent_type,
    el.event_data->>'updated_by' AS updated_by_user_id,
    u.email AS updated_by_email,
    el.event_data->>'is_enabled' AS is_enabled,
    el.event_data->>'config_changes' AS config_changes
FROM event_logs el
LEFT JOIN users u ON (el.event_data->>'updated_by')::VARCHAR = u.id
WHERE el.event_type = 'CONFIG_UPDATED'
ORDER BY el.created_at DESC
LIMIT 50;

-- =============================================
-- TEAM METRICS & ANALYTICS
-- =============================================

-- Get team quality score trend (last 7 days)
SELECT 
    DATE(cr.created_at) AS analysis_date,
    COUNT(*) AS analyses_count,
    ROUND(AVG(cr.quality_score), 2) AS avg_quality_score,
    COUNT(CASE WHEN cr.quality_score >= 80 THEN 1 END) AS high_quality_count,
    COUNT(CASE WHEN cr.quality_score < 50 THEN 1 END) AS low_quality_count
FROM code_reviews cr
WHERE cr.status = 'COMPLETED'
  AND cr.created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(cr.created_at)
ORDER BY analysis_date;

-- Get user leaderboard (best quality scores)
SELECT 
    u.name,
    u.email,
    COUNT(cr.id) AS total_analyses,
    ROUND(AVG(cr.quality_score), 2) AS avg_quality_score,
    MAX(cr.quality_score) AS best_score
FROM users u
INNER JOIN code_reviews cr ON u.id = cr.user_id
WHERE cr.status = 'COMPLETED'
  AND cr.created_at >= NOW() - INTERVAL '30 days'
GROUP BY u.id, u.name, u.email
HAVING COUNT(cr.id) >= 5
ORDER BY avg_quality_score DESC
LIMIT 10;

-- =============================================
-- EXPORT LOGS & COMPLIANCE
-- =============================================

-- Get export audit trail
SELECT 
    ael.id,
    ael.user_id,
    u.email,
    cr.filename,
    ael.export_format,
    ael.file_size_bytes,
    ael.created_at
FROM analysis_export_logs ael
INNER JOIN users u ON ael.user_id = u.id
INNER JOIN code_reviews cr ON ael.review_id = cr.id
WHERE ael.created_at >= NOW() - INTERVAL '30 days'
ORDER BY ael.created_at DESC;

-- Get most exported analyses
SELECT 
    cr.id,
    cr.filename,
    cr.quality_score,
    COUNT(ael.id) AS export_count,
    MAX(ael.created_at) AS last_exported_at
FROM code_reviews cr
INNER JOIN analysis_export_logs ael ON cr.id = ael.review_id
GROUP BY cr.id
HAVING COUNT(ael.id) >= 2
ORDER BY export_count DESC, last_exported_at DESC
LIMIT 20;

-- =============================================
-- CLEANUP & MAINTENANCE
-- =============================================

-- Delete old completed reviews (retention: 90 days)
DELETE FROM code_reviews
WHERE status = 'COMPLETED'
  AND completed_at < NOW() - INTERVAL '90 days';

-- Delete old event logs (retention: 30 days)
DELETE FROM event_logs
WHERE created_at < NOW() - INTERVAL '30 days';

-- Vacuum and analyze tables (maintenance job)
VACUUM ANALYZE users;
VACUUM ANALYZE code_reviews;
VACUUM ANALYZE agent_findings;
VACUUM ANALYZE ai_usage_metrics;
VACUUM ANALYZE mcp_context_logs;
VACUUM ANALYZE event_logs;
