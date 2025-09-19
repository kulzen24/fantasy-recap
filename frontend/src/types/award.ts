/**
 * Award types for custom weekly awards system
 * Corresponds to backend models in app/models/award.py
 */

export enum AwardType {
  TEAM_PERFORMANCE = "team_performance",
  PLAYER_PERFORMANCE = "player_performance", 
  MATCHUP_BASED = "matchup_based",
  SEASON_LONG = "season_long",
  CUSTOM = "custom"
}

export enum AwardFrequency {
  WEEKLY = "weekly",
  MONTHLY = "monthly",
  SEASON = "season", 
  PLAYOFF = "playoff"
}

export enum AwardStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  ARCHIVED = "archived"
}

export interface AwardCriteria {
  type: AwardType
  
  // Performance-based criteria
  stat_category?: string
  comparison?: string
  threshold?: number
  
  // Matchup-based criteria  
  margin_type?: string
  
  // Custom criteria
  custom_formula?: string
  custom_description?: string
  
  // Additional metadata
  metadata?: Record<string, any>
}

export interface Award {
  id: string
  user_id: string
  league_id: string
  
  // Award details
  name: string
  description?: string
  emoji?: string
  
  // Award configuration
  criteria: AwardCriteria
  frequency: AwardFrequency
  status: AwardStatus
  
  // Metadata
  created_at: string
  updated_at: string
  
  // Usage tracking
  times_awarded: number
  last_awarded_week?: number
  last_awarded_season?: number
  
  // Settings
  is_public: boolean
  auto_assign: boolean
  
  // Custom styling
  color?: string
  icon_url?: string
}

export interface AwardWinner {
  id: string
  award_id: string
  
  // Timing
  week: number
  season: number
  
  // Winner details
  winner_type: string
  winner_id: string
  winner_name: string
  platform: string
  
  // Award context
  reason?: string
  stats: Record<string, number>
  
  // Metadata
  awarded_at: string
  awarded_by?: string
  
  // Display
  highlight_message?: string
}

export interface AwardCreateRequest {
  league_id: string
  name: string
  description?: string
  emoji?: string
  criteria: AwardCriteria
  frequency?: AwardFrequency
  is_public?: boolean
  auto_assign?: boolean
  color?: string
}

export interface AwardUpdateRequest {
  name?: string
  description?: string
  emoji?: string
  criteria?: AwardCriteria
  frequency?: AwardFrequency
  status?: AwardStatus
  is_public?: boolean
  auto_assign?: boolean
  color?: string
}

export interface AwardWinnerAssignRequest {
  week: number
  season: number
  winner_type: string
  winner_id: string
  winner_name: string
  platform: string
  reason?: string
  stats?: Record<string, number>
  highlight_message?: string
}

export interface AwardTemplate {
  id: string
  name: string
  description: string
  emoji: string
  criteria: AwardCriteria
  frequency: AwardFrequency
  category: string
  tags: string[]
  is_popular: boolean
  usage_count: number
}

export interface AwardResponse {
  success: boolean
  data?: Award
  error?: string
  message?: string
}

export interface AwardListResponse {
  success: boolean
  data?: Award[]
  total?: number
  page?: number
  per_page?: number
  error?: string
}

export interface AwardWinnerResponse {
  success: boolean
  data?: AwardWinner
  error?: string
  message?: string
}

export interface AwardWinnerListResponse {
  success: boolean
  data?: AwardWinner[]
  total?: number
  error?: string
}

export interface AwardTemplateResponse {
  success: boolean
  data?: AwardTemplate[]
  categories?: string[]
  error?: string
}

// Helper types for UI components
export type AwardFormData = Omit<AwardCreateRequest, 'league_id'> & {
  league_id?: string
}

export interface AwardCriteriaFormData {
  type: AwardType
  stat_category: string
  comparison: string
  threshold: string
  margin_type: string
  custom_formula: string
  custom_description: string
}

export interface AwardDisplaySettings {
  color: string
  emoji: string
  icon_url: string
}
