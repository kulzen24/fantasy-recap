// API Response Types
export interface APIResponse<T> {
  success: boolean
  data: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T> extends APIResponse<T[]> {
  count: number
  has_more?: boolean
  total?: number
}

// User and Auth Types
export interface User {
  id: string
  email: string
  display_name?: string
  avatar_url?: string
  timezone: string
  created_at: string
  updated_at: string
}

export interface AuthStatus {
  authenticated: boolean
  user: User | null
  message?: string
}

// League Types
export interface League {
  id: string
  user_id: string
  platform: 'yahoo' | 'espn' | 'sleeper'
  league_id: string
  league_name: string
  season: number
  is_active: boolean
  created_at: string
  updated_at: string
  league_data: {
    total_teams: number
    current_week: number
    scoring_type: string
    teams: any[]
    last_sync: string
    metadata?: any
  }
}

export interface LeagueStats {
  total_leagues: number
  active_leagues: number
  platforms: {
    yahoo: number
    espn: number
    sleeper: number
  }
  last_sync?: string
}

// Recap Types
export interface Recap {
  id: string
  user_id: string
  league_id: string
  week: number
  season: number
  title: string
  content: string
  tone: string
  length: string
  quality_score?: number
  created_at: string
  updated_at: string
  league_name?: string
  status: 'pending' | 'generating' | 'completed' | 'failed'
}

export interface RecapGenerationRequest {
  league_id: string
  week: number
  season: number
  tone: string
  length: string
  include_awards: boolean
  include_predictions: boolean
  focus_on_user_team: boolean
  template_id?: string
}

export interface RecapStats {
  total_recaps: number
  avg_quality_score: number
  recent_recaps: number
  favorite_tone: string
  weekly_breakdown: { [key: string]: number }
}

// Provider and LLM Types
export interface ProviderPreferences {
  primary_provider: string
  fallback_provider?: string
  preferences: {
    tone_preference: string
    length_preference: string
    include_awards_default: boolean
  }
}

export interface APIKeyInfo {
  provider: string
  is_valid: boolean
  masked_key: string
  created_at: string
  last_validated?: string
}

// Template Types
export interface Template {
  id: string
  user_id: string
  file_name: string
  file_format: string
  user_notes?: string
  tags?: string[]
  status: 'uploaded' | 'analyzing' | 'analyzed' | 'error'
  created_at: string
  updated_at: string
  style_analysis?: {
    tone: string
    writing_style: string
    complexity_score: number
    key_phrases: string[]
  }
}

export interface TemplateStats {
  total_templates: number
  analyzed_templates: number
  active_templates: number
  most_used_tone: string
}

// NLQ (Natural Language Query) Types
export interface NLQQuery {
  query: string
  context?: {
    league_id?: string
    week?: number
    season?: number
  }
}

export interface NLQResponse {
  success: boolean
  response: string
  data?: any
  confidence_score?: number
  query_type?: string
  execution_time?: number
}

// Error Types
export interface APIError {
  message: string
  details?: any
  status_code?: number
  error_code?: string
}