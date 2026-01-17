-- ============================================================================
-- SR&ED - DEVELOPMENT ONLY Database Setup
-- ============================================================================
--
-- WARNING: DO NOT USE IN PRODUCTION!
--
-- This script is for SCRATCH/DEVELOPMENT environments only.
-- It drops and recreates the entire schema, destroying all data.
--
-- FOR PRODUCTION, use:
--   1. Alembic migrations: `alembic upgrade head`
--   2. RLS setup: `psql -f apply-rls.sql`
--
-- This file exists for quick local development resets and may be
-- out of sync with the actual Alembic-managed schema.
--
-- ============================================================================

-- CLEANUP: Drop existing schema to ensure clean slate
DROP SCHEMA IF EXISTS sred_ds CASCADE;

-- Create schema for the application
CREATE SCHEMA IF NOT EXISTS sred_ds;

-- Set search path so all subsequent commands affect this schema
SET search_path TO sred_ds, public;

-- Enable required extensions (in public schema)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;
CREATE EXTENSION IF NOT EXISTS "pgcrypto" SCHEMA public;
CREATE EXTENSION IF NOT EXISTS "vector" SCHEMA public;

-- Create roles (MUST be done before policies reference them)
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
      WHERE  rolname = 'sred_app') THEN

      CREATE ROLE sred_app WITH LOGIN PASSWORD 'your_secure_password_here';
   END IF;
END
$do$;

-- Create companies table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    name TEXT NOT NULL,
    subdomain TEXT UNIQUE,
    plan_tier TEXT DEFAULT 'starter' CHECK (plan_tier IN ('starter', 'professional', 'enterprise')),
    tenancy_type TEXT DEFAULT 'shared_rls' CHECK (tenancy_type IN ('shared_rls', 'dedicated_schema', 'dedicated_instance')),
    settings JSONB DEFAULT '{}',
    subscription_status TEXT DEFAULT 'trial' CHECK (subscription_status IN ('trial', 'active', 'cancelled', 'suspended')),
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    first_name TEXT,
    last_name TEXT,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT false,
    is_company_admin BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create groups table
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    permissions_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, name)
);

-- Create user_groups junction table
CREATE TABLE user_groups (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, group_id)
);

-- Create documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    s3_path TEXT NOT NULL,
    file_size BIGINT,
    mime_type TEXT,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    access_groups_json JSONB DEFAULT '[]',
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'error')),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document_chunks table for RAG
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- OpenAI ada-002 embedding size
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

-- Create conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'ai')),
    metadata JSONB DEFAULT '{}',
    rating TEXT CHECK (rating IN ('up', 'down')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see their own company's data
CREATE POLICY company_isolation_users ON users
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

CREATE POLICY company_isolation_groups ON groups
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

CREATE POLICY company_isolation_documents ON documents
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

CREATE POLICY company_isolation_conversations ON conversations
    FOR ALL TO authenticated_users
    USING (company_id = current_setting('app.current_company_id', true)::UUID);

-- Create indexes for performance
CREATE INDEX idx_users_company_id ON users(company_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_groups_company_id ON groups(company_id);
CREATE INDEX idx_documents_company_id ON documents(company_id);
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_conversations_company_id ON conversations(company_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default groups for new companies
CREATE OR REPLACE FUNCTION create_default_groups()
RETURNS TRIGGER AS $$
BEGIN
    -- Create default groups for new company
    INSERT INTO groups (company_id, name, description, permissions_json) VALUES
    (NEW.id, 'Administrators', 'Full system access', '{
        "users": {"create": true, "read": true, "update": true, "delete": true},
        "documents": {"create": true, "read": true, "update": true, "delete": true},
        "conversations": {"create": true, "read": true, "update": true, "delete": true},
        "company": {"read": true, "update": true}
    }'),
    (NEW.id, 'Partners', 'High-level access for partners', '{
        "users": {"create": true, "read": true, "update": false, "delete": false},
        "documents": {"create": true, "read": true, "update": true, "delete": true},
        "conversations": {"create": true, "read": true, "update": true, "delete": true},
        "company": {"read": true, "update": false}
    }'),
    (NEW.id, 'Associates', 'Standard access for associates', '{
        "users": {"create": false, "read": true, "update": false, "delete": false},
        "documents": {"create": true, "read": true, "update": false, "delete": false},
        "conversations": {"create": true, "read": true, "update": true, "delete": false},
        "company": {"read": false, "update": false}
    }'),
    (NEW.id, 'Contractors', 'Limited access for Contractors', '{
        "users": {"create": false, "read": false, "update": false, "delete": false},
        "documents": {"create": false, "read": true, "update": false, "delete": false},
        "conversations": {"create": true, "read": true, "update": true, "delete": false},
        "company": {"read": false, "update": false}
    }'),
    (NEW.id, 'Guests', 'Read-only access for guests', '{
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

-- Grant permissions (schema usage is key here)
GRANT USAGE ON SCHEMA sred_ds TO sred_app;
GRANT USAGE ON SCHEMA public TO sred_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sred_ds TO sred_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sred_ds TO sred_app;

-- Grant permissions for RLS
GRANT authenticated_users TO sred_app;