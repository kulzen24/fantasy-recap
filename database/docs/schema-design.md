# Fantasy Recaps Database Schema Design

## Overview

This document describes the database schema for the Fantasy Football Recap Generator application using Supabase (PostgreSQL). The schema follows 2024 best practices for security, performance, and maintainability.

## Security Principles

1. **Row Level Security (RLS)** enabled on all user-data tables
2. **API keys encrypted** using `pgcrypto` extension
3. **No password storage** - OAuth tokens only
4. **UUID primary keys** to prevent enumeration attacks
5. **Audit logging** for sensitive operations

## Tables

### 1. User Profiles (`user_profiles`)

Extends Supabase's built-in `auth.users` table with application-specific data.

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    avatar_url TEXT,
    timezone TEXT DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**RLS Policy:**
```sql
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view and edit their own profile"
    ON user_profiles FOR ALL
    USING (auth.uid() = id);
```

### 2. User OAuth Providers (`user_oauth_providers`)

Manages OAuth connections for SSO (Google, Yahoo, ESPN, Sleeper).

```sql
CREATE TABLE user_oauth_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL, -- 'google', 'yahoo', 'espn', 'sleeper'
    provider_user_id TEXT NOT NULL,
    access_token_encrypted BYTEA,
    refresh_token_encrypted BYTEA,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, provider, provider_user_id)
);
```

**RLS Policy:**
```sql
ALTER TABLE user_oauth_providers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own OAuth providers"
    ON user_oauth_providers FOR ALL
    USING (auth.uid() = user_id);
```

### 3. User API Keys (`user_api_keys`)

Stores encrypted LLM provider API keys (OpenAI, Anthropic, Google).

```sql
CREATE TABLE user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL, -- 'openai', 'anthropic', 'google'
    api_key_encrypted BYTEA NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, provider)
);
```

**RLS Policy:**
```sql
ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own API keys"
    ON user_api_keys FOR ALL
    USING (auth.uid() = user_id);
```

### 4. Fantasy Leagues (`fantasy_leagues`)

Connected fantasy football leagues from various platforms.

```sql
CREATE TABLE fantasy_leagues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL, -- 'yahoo', 'espn', 'sleeper'
    league_id TEXT NOT NULL, -- Platform-specific league ID
    league_name TEXT NOT NULL,
    season INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    league_data JSONB DEFAULT '{}', -- Platform-specific metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, platform, league_id, season)
);
```

**RLS Policy:**
```sql
ALTER TABLE fantasy_leagues ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own fantasy leagues"
    ON fantasy_leagues FOR ALL
    USING (auth.uid() = user_id);
```

### 5. User Template Samples (`user_template_samples`)

User-uploaded writing samples for style analysis.

```sql
CREATE TABLE user_template_samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    style_analysis JSONB, -- AI-analyzed style features
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**RLS Policy:**
```sql
ALTER TABLE user_template_samples ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own template samples"
    ON user_template_samples FOR ALL
    USING (auth.uid() = user_id);
```

### 6. Generated Recaps (`generated_recaps`)

AI-generated and user-edited fantasy football recaps.

```sql
CREATE TABLE generated_recaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    league_id UUID NOT NULL REFERENCES fantasy_leagues(id) ON DELETE CASCADE,
    week INTEGER NOT NULL,
    season INTEGER NOT NULL,
    title TEXT NOT NULL,
    original_content TEXT NOT NULL, -- AI-generated content
    edited_content TEXT, -- User-edited content
    generation_metadata JSONB DEFAULT '{}', -- Model used, parameters, etc.
    is_published BOOLEAN DEFAULT false,
    llm_provider TEXT NOT NULL, -- 'openai', 'anthropic', 'google'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(league_id, week, season)
);
```

**RLS Policy:**
```sql
ALTER TABLE generated_recaps ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage recaps for their own leagues"
    ON generated_recaps FOR ALL
    USING (auth.uid() = user_id);
```

### 7. Weekly Awards (`weekly_awards`)

User-defined custom weekly awards.

```sql
CREATE TABLE weekly_awards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    league_id UUID NOT NULL REFERENCES fantasy_leagues(id) ON DELETE CASCADE,
    award_name TEXT NOT NULL,
    award_description TEXT,
    criteria JSONB DEFAULT '{}', -- Award criteria definition
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**RLS Policy:**
```sql
ALTER TABLE weekly_awards ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage awards for their own leagues"
    ON weekly_awards FOR ALL
    USING (auth.uid() = user_id);
```

### 8. Award Winners (`award_winners`)

Records of weekly award recipients.

```sql
CREATE TABLE award_winners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    award_id UUID NOT NULL REFERENCES weekly_awards(id) ON DELETE CASCADE,
    week INTEGER NOT NULL,
    season INTEGER NOT NULL,
    team_id TEXT NOT NULL, -- Platform-specific team ID
    team_name TEXT NOT NULL,
    reason TEXT,
    stats JSONB DEFAULT '{}', -- Supporting statistics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(award_id, week, season)
);
```

**RLS Policy:**
```sql
ALTER TABLE award_winners ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view award winners for their own awards"
    ON award_winners FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM weekly_awards 
            WHERE weekly_awards.id = award_winners.award_id 
            AND weekly_awards.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage award winners for their own awards"
    ON award_winners FOR INSERT, UPDATE, DELETE
    USING (
        EXISTS (
            SELECT 1 FROM weekly_awards 
            WHERE weekly_awards.id = award_winners.award_id 
            AND weekly_awards.user_id = auth.uid()
        )
    );
```

## Indexes

```sql
-- Performance indexes
CREATE INDEX idx_user_profiles_created_at ON user_profiles(created_at);
CREATE INDEX idx_fantasy_leagues_user_platform ON fantasy_leagues(user_id, platform);
CREATE INDEX idx_fantasy_leagues_season ON fantasy_leagues(season);
CREATE INDEX idx_generated_recaps_league_week ON generated_recaps(league_id, week, season);
CREATE INDEX idx_generated_recaps_user_created ON generated_recaps(user_id, created_at);
CREATE INDEX idx_weekly_awards_league ON weekly_awards(league_id);
CREATE INDEX idx_award_winners_award_week ON award_winners(award_id, week, season);
```

## Functions

### Encryption Functions

```sql
-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data BYTEA)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(encrypted_data, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Trigger Functions

```sql
-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_oauth_providers_updated_at 
    BEFORE UPDATE ON user_oauth_providers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- (Repeat for all tables with updated_at column)
```

## Security Notes

1. **Encryption Key Management**: The encryption key should be stored securely in environment variables and never in the database or code.

2. **API Key Access**: API keys should only be decrypted in the backend service layer, never exposed to the frontend.

3. **RLS Testing**: All RLS policies should be thoroughly tested to ensure users cannot access other users' data.

4. **Audit Logging**: Consider adding audit tables for sensitive operations like API key access and recap generation.

## Migration Strategy

1. Create tables in dependency order
2. Enable RLS on all tables
3. Create RLS policies
4. Add indexes
5. Create functions and triggers
6. Test with sample data
7. Verify security policies

## Performance Considerations

- Use appropriate indexes for common query patterns
- Consider partitioning large tables by season/year if data volume grows
- Monitor query performance and add indexes as needed
- Use materialized views for complex aggregations if necessary
