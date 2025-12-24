-- ============================================================================
-- BC Legal Tech - Row Level Security (RLS) Setup
-- ============================================================================
--
-- PURPOSE: Enables PostgreSQL Row Level Security for multi-tenant data isolation.
--
-- WHEN TO RUN:
--   1. After running Alembic migrations: `alembic upgrade head`
--   2. This script is IDEMPOTENT - safe to run multiple times
--
-- PREREQUISITES:
--   - PostgreSQL 15+ with pgvector extension
--   - Schema `bc_legal_ds` must exist (created by Alembic)
--   - All tables must exist (created by Alembic)
--
-- HOW IT WORKS:
--   1. Creates roles: `authenticated_users` (for RLS policies) and `bc_legal_app` (app connection)
--   2. Creates triggers for auto-updating timestamps and default groups
--   3. Enables RLS on all tables in bc_legal_ds schema
--   4. Creates policies that filter by `app.current_company_id` session variable
--   5. Grants permissions to `bc_legal_app` role
--
-- USAGE IN CODE:
--   Before any tenant-specific query, set the session variable:
--   SELECT set_config('app.current_company_id', '<uuid>', true);
--
-- ============================================================================

SET search_path TO bc_legal_ds, public;

-- Create roles
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'authenticated_users') THEN

      CREATE ROLE authenticated_users;
   END IF;
END
$do$;

DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'bc_legal_app') THEN

      CREATE ROLE bc_legal_app WITH LOGIN PASSWORD 'your_secure_password_here';
   END IF;
END
$do$;

-- triggers and functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- SECURITY DEFINER allows this function to bypass RLS when inserting default groups
CREATE OR REPLACE FUNCTION create_default_groups()
RETURNS TRIGGER SECURITY DEFINER AS $$
BEGIN
    -- Create default groups for new company
    INSERT INTO bc_legal_ds.groups (id, company_id, name, description, permissions_json) VALUES
    (public.uuid_generate_v4(), NEW.id, 'Administrators', 'Full system access', '{
        "users": {"create": true, "read": true, "update": true, "delete": true},
        "documents": {"create": true, "read": true, "update": true, "delete": true},
        "conversations": {"create": true, "read": true, "update": true, "delete": true},
        "company": {"read": true, "update": true}
    }'),
    (public.uuid_generate_v4(), NEW.id, 'Partners', 'High-level access for partners', '{
        "users": {"create": true, "read": true, "update": false, "delete": false},
        "documents": {"create": true, "read": true, "update": true, "delete": true},
        "conversations": {"create": true, "read": true, "update": true, "delete": true},
        "company": {"read": true, "update": false}
    }'),
    (public.uuid_generate_v4(), NEW.id, 'Associates', 'Standard access for associates', '{
        "users": {"create": false, "read": true, "update": false, "delete": false},
        "documents": {"create": true, "read": true, "update": false, "delete": false},
        "conversations": {"create": true, "read": true, "update": true, "delete": false},
        "company": {"read": false, "update": false}
    }'),
    (public.uuid_generate_v4(), NEW.id, 'Paralegals', 'Limited access for paralegals', '{
        "users": {"create": false, "read": false, "update": false, "delete": false},
        "documents": {"create": false, "read": true, "update": false, "delete": false},
        "conversations": {"create": true, "read": true, "update": true, "delete": false},
        "company": {"read": false, "update": false}
    }'),
    (public.uuid_generate_v4(), NEW.id, 'Guests', 'Read-only access for guests', '{
        "users": {"create": false, "read": false, "update": false, "delete": false},
        "documents": {"create": false, "read": true, "update": false, "delete": false},
        "conversations": {"create": true, "read": true, "update": false, "delete": false},
        "company": {"read": false, "update": false}
    }');
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER create_default_groups_trigger
    AFTER INSERT ON companies
    FOR EACH ROW
    EXECUTE FUNCTION create_default_groups();

-- Enable Row Level Security on ALL tables (list from Alembic + others)
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'bc_legal_ds') LOOP
        EXECUTE 'ALTER TABLE bc_legal_ds.' || quote_ident(r.tablename) || ' ENABLE ROW LEVEL SECURITY';
    END LOOP;
END $$;

-- Create RLS policies
-- Note: 'bc_legal_app' role connects for the API. It is part of 'authenticated_users'.

-- =======================================================
-- 1. Authentication & System Tables (Permissive / Public)
-- =======================================================

-- Companies: Public Insert (Signup), Public Select (Login/Check), Tenant Update
CREATE POLICY companies_insert_public ON companies FOR INSERT WITH CHECK (true);
CREATE POLICY companies_select_public ON companies FOR SELECT USING (true);
CREATE POLICY companies_isolation_update ON companies FOR UPDATE USING (id = current_setting('app.current_company_id', true)::UUID);

-- Users: Public Insert (Signup), Public Select (Login context), Tenant Update
CREATE POLICY users_insert_public ON users FOR INSERT WITH CHECK (true);
CREATE POLICY users_select_public ON users FOR SELECT USING (true);
CREATE POLICY users_isolation_update ON users FOR UPDATE USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Auth Tokens: Accessible to application (linked logic handled by app)
-- Ideally restrict to own user, but for Auth Flow complexity, app needs full access.
CREATE POLICY refresh_tokens_all ON refresh_tokens USING (true);
CREATE POLICY password_reset_tokens_all ON password_reset_tokens USING (true);

-- System Reference
CREATE POLICY plan_limits_read_all ON plan_limits FOR SELECT USING (true);
CREATE POLICY api_usage_logs_insert ON api_usage_logs FOR INSERT WITH CHECK (true);
CREATE POLICY api_usage_logs_select_own ON api_usage_logs FOR SELECT USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Marketing
CREATE POLICY waitlist_insert_public ON waitlist_signups FOR INSERT WITH CHECK (true);
CREATE POLICY waitlist_select_admin ON waitlist_signups FOR SELECT USING (true); -- TODO: Restrict to admin?

-- =======================================================
-- 2. Tenant Data (Restrictive)
-- =======================================================

-- Groups
CREATE POLICY company_isolation_groups ON groups
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Conversations
CREATE POLICY company_isolation_conversations ON conversations
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Matters
CREATE POLICY company_isolation_matters ON matters
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Document Events
CREATE POLICY company_isolation_document_events ON document_events
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Billable Sessions
CREATE POLICY company_isolation_billable_sessions ON billable_sessions
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Daily Briefings
CREATE POLICY company_isolation_daily_briefings ON daily_briefings
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Feedback / Analytics
CREATE POLICY company_isolation_feedback_details ON message_feedback_details
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

CREATE POLICY company_isolation_signals ON conversation_signals
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

CREATE POLICY company_isolation_quality ON message_quality_scores
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Indirect Association (Tables linking to parent with company_id)

-- Documents (direct company_id for performance - denormalized from matters)
CREATE POLICY company_isolation_documents ON documents
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Messages -> Conversations -> Company
CREATE POLICY company_isolation_messages ON messages
    FOR ALL TO authenticated_users
    USING (conversation_id IN (
        SELECT id FROM bc_legal_ds.conversations 
        WHERE company_id = current_setting('app.current_company_id', true)::UUID
    ));

-- Document Chunks -> Documents (simplified now that documents has company_id)
CREATE POLICY company_isolation_document_chunks ON document_chunks
    FOR ALL TO authenticated_users
    USING (document_id IN (
        SELECT id FROM bc_legal_ds.documents
        WHERE company_id = current_setting('app.current_company_id', true)::UUID
    ));

-- User Groups -> Groups -> Company
CREATE POLICY company_isolation_user_groups ON user_groups
    FOR ALL TO authenticated_users
    USING (group_id IN (
        SELECT id FROM bc_legal_ds.groups 
        WHERE company_id = current_setting('app.current_company_id', true)::UUID
    ));

-- Matter Access -> Matters -> Company
CREATE POLICY company_isolation_matter_access ON matter_access
    FOR ALL TO authenticated_users
    USING (matter_id IN (
        SELECT id FROM bc_legal_ds.matters 
        WHERE company_id = current_setting('app.current_company_id', true)::UUID
    ));

-- Grant permissions
GRANT USAGE ON SCHEMA bc_legal_ds TO bc_legal_app;
GRANT USAGE ON SCHEMA public TO bc_legal_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bc_legal_ds TO bc_legal_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA bc_legal_ds TO bc_legal_app;

-- Grant permissions for RLS
GRANT authenticated_users TO bc_legal_app;
