-- Fantasy Recaps Database Schema
-- Migration 001: Initial Schema Creation (Simplified for Supabase)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- 1. USER PROFILES TABLE
-- =====================================================

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    avatar_url TEXT,
    timezone TEXT DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS and create policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view and edit their own profile"
    ON user_profiles FOR ALL
    USING (auth.uid() = id);

-- =====================================================
-- 2. USER OAUTH PROVIDERS TABLE
-- =====================================================

CREATE TABLE user_oauth_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('google', 'yahoo', 'espn', 'sleeper')),
    provider_user_id TEXT NOT NULL,
    access_token_encrypted TEXT, -- We'll encrypt this in the application layer
    refresh_token_encrypted TEXT, -- We'll encrypt this in the application layer
    token_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, provider, provider_user_id)
);

-- Enable RLS and create policies
ALTER TABLE user_oauth_providers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own OAuth providers"
    ON user_oauth_providers FOR ALL
    USING (auth.uid() = user_id);

-- =====================================================
-- 3. USER API KEYS TABLE
-- =====================================================

CREATE TABLE user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('openai', 'anthropic', 'google')),
    api_key_encrypted TEXT NOT NULL, -- We'll encrypt this in the application layer
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- Enable RLS and create policies
ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own API keys"
    ON user_api_keys FOR ALL
    USING (auth.uid() = user_id);

-- =====================================================
-- 4. FANTASY LEAGUES TABLE
-- =====================================================

CREATE TABLE fantasy_leagues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('yahoo', 'espn', 'sleeper')),
    league_id TEXT NOT NULL,
    league_name TEXT NOT NULL,
    season INTEGER NOT NULL CHECK (season >= 2000 AND season <= 2050),
    is_active BOOLEAN DEFAULT true,
    league_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, platform, league_id, season)
);

-- Enable RLS and create policies
ALTER TABLE fantasy_leagues ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own fantasy leagues"
    ON fantasy_leagues FOR ALL
    USING (auth.uid() = user_id);

-- =====================================================
-- 5. USER TEMPLATE SAMPLES TABLE
-- =====================================================

CREATE TABLE user_template_samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    style_analysis JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS and create policies
ALTER TABLE user_template_samples ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own template samples"
    ON user_template_samples FOR ALL
    USING (auth.uid() = user_id);

-- =====================================================
-- 6. GENERATED RECAPS TABLE
-- =====================================================

CREATE TABLE generated_recaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    league_id UUID NOT NULL REFERENCES fantasy_leagues(id) ON DELETE CASCADE,
    week INTEGER NOT NULL CHECK (week >= 1 AND week <= 20),
    season INTEGER NOT NULL CHECK (season >= 2000 AND season <= 2050),
    title TEXT NOT NULL,
    original_content TEXT NOT NULL,
    edited_content TEXT,
    generation_metadata JSONB DEFAULT '{}',
    is_published BOOLEAN DEFAULT false,
    llm_provider TEXT NOT NULL CHECK (llm_provider IN ('openai', 'anthropic', 'google')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(league_id, week, season)
);

-- Enable RLS and create policies
ALTER TABLE generated_recaps ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage recaps for their own leagues"
    ON generated_recaps FOR ALL
    USING (auth.uid() = user_id);

-- =====================================================
-- 7. WEEKLY AWARDS TABLE
-- =====================================================

CREATE TABLE weekly_awards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    league_id UUID NOT NULL REFERENCES fantasy_leagues(id) ON DELETE CASCADE,
    award_name TEXT NOT NULL,
    award_description TEXT,
    criteria JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS and create policies
ALTER TABLE weekly_awards ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage awards for their own leagues"
    ON weekly_awards FOR ALL
    USING (auth.uid() = user_id);

-- =====================================================
-- 8. AWARD WINNERS TABLE
-- =====================================================

CREATE TABLE award_winners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    award_id UUID NOT NULL REFERENCES weekly_awards(id) ON DELETE CASCADE,
    week INTEGER NOT NULL CHECK (week >= 1 AND week <= 20),
    season INTEGER NOT NULL CHECK (season >= 2000 AND season <= 2050),
    team_id TEXT NOT NULL,
    team_name TEXT NOT NULL,
    reason TEXT,
    stats JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(award_id, week, season)
);

-- Enable RLS and create policies
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

CREATE POLICY "Users can insert award winners for their own awards"
    ON award_winners FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM weekly_awards 
            WHERE weekly_awards.id = award_winners.award_id 
            AND weekly_awards.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update award winners for their own awards"
    ON award_winners FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM weekly_awards 
            WHERE weekly_awards.id = award_winners.award_id 
            AND weekly_awards.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete award winners for their own awards"
    ON award_winners FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM weekly_awards 
            WHERE weekly_awards.id = award_winners.award_id 
            AND weekly_awards.user_id = auth.uid()
        )
    );

-- =====================================================
-- 9. PERFORMANCE INDEXES
-- =====================================================

-- User profiles
CREATE INDEX idx_user_profiles_created_at ON user_profiles(created_at);

-- OAuth providers
CREATE INDEX idx_user_oauth_providers_user_provider ON user_oauth_providers(user_id, provider);

-- API keys
CREATE INDEX idx_user_api_keys_user_provider ON user_api_keys(user_id, provider);
CREATE INDEX idx_user_api_keys_last_used ON user_api_keys(last_used_at);

-- Fantasy leagues
CREATE INDEX idx_fantasy_leagues_user_platform ON fantasy_leagues(user_id, platform);
CREATE INDEX idx_fantasy_leagues_season ON fantasy_leagues(season);
CREATE INDEX idx_fantasy_leagues_active ON fantasy_leagues(is_active);

-- Template samples
CREATE INDEX idx_user_template_samples_user_active ON user_template_samples(user_id, is_active);

-- Generated recaps
CREATE INDEX idx_generated_recaps_league_week ON generated_recaps(league_id, week, season);
CREATE INDEX idx_generated_recaps_user_created ON generated_recaps(user_id, created_at);
CREATE INDEX idx_generated_recaps_published ON generated_recaps(is_published);

-- Weekly awards
CREATE INDEX idx_weekly_awards_league ON weekly_awards(league_id);
CREATE INDEX idx_weekly_awards_active ON weekly_awards(is_active);

-- Award winners
CREATE INDEX idx_award_winners_award_week ON award_winners(award_id, week, season);

-- =====================================================
-- 10. UPDATE TRIGGERS
-- =====================================================

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

CREATE TRIGGER update_user_api_keys_updated_at 
    BEFORE UPDATE ON user_api_keys 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fantasy_leagues_updated_at 
    BEFORE UPDATE ON fantasy_leagues 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_template_samples_updated_at 
    BEFORE UPDATE ON user_template_samples 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_generated_recaps_updated_at 
    BEFORE UPDATE ON generated_recaps 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_weekly_awards_updated_at 
    BEFORE UPDATE ON weekly_awards 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 001_initial_schema_simplified.sql completed successfully';
    RAISE NOTICE 'Note: API key encryption will be handled in the application layer';
END $$;
