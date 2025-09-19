/**
 * Award Creation and Editing Form Component
 * Handles creating new awards and editing existing ones
 */

import React, { useState, useEffect, useCallback } from 'react'
import { 
  Award,
  AwardCreateRequest,
  AwardUpdateRequest,
  AwardType,
  AwardFrequency,
  AwardCriteria,
  AwardCriteriaFormData
} from '../../types/award'
import { useCreateAward, useUpdateAward, useAwardTemplates } from '../../hooks/useAwards'

interface AwardFormProps {
  award?: Award
  leagueId?: string
  onSuccess?: (award: Award) => void
  onCancel?: () => void
  className?: string
}

interface FormErrors {
  [key: string]: string
}

export function AwardForm({ award, leagueId, onSuccess, onCancel, className = '' }: AwardFormProps) {
  const isEditing = !!award
  const createAward = useCreateAward()
  const updateAward = useUpdateAward()
  const { data: templatesData } = useAwardTemplates()
  
  // Form state
  const [formData, setFormData] = useState({
    name: award?.name || '',
    description: award?.description || '',
    emoji: award?.emoji || '🏆',
    frequency: award?.frequency || AwardFrequency.WEEKLY,
    is_public: award?.is_public || false,
    auto_assign: award?.auto_assign || false,
    color: award?.color || '#fbbf24'
  })
  
  const [criteriaData, setCriteriaData] = useState<AwardCriteriaFormData>({
    type: award?.criteria.type || AwardType.TEAM_PERFORMANCE,
    stat_category: award?.criteria.stat_category || '',
    comparison: award?.criteria.comparison || 'highest',
    threshold: award?.criteria.threshold?.toString() || '',
    margin_type: award?.criteria.margin_type || '',
    custom_formula: award?.criteria.custom_formula || '',
    custom_description: award?.criteria.custom_description || ''
  })
  
  const [errors, setErrors] = useState<FormErrors>({})
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  
  // Validation
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}
    
    if (!formData.name.trim()) {
      newErrors.name = 'Award name is required'
    }
    
    if (formData.name.length > 100) {
      newErrors.name = 'Award name must be 100 characters or less'
    }
    
    if (formData.description && formData.description.length > 500) {
      newErrors.description = 'Description must be 500 characters or less'
    }
    
    // Validate criteria based on type
    if (criteriaData.type === AwardType.TEAM_PERFORMANCE || criteriaData.type === AwardType.PLAYER_PERFORMANCE) {
      if (!criteriaData.stat_category) {
        newErrors.stat_category = 'Stat category is required for performance awards'
      }
      if (!criteriaData.comparison) {
        newErrors.comparison = 'Comparison type is required'
      }
    }
    
    if (criteriaData.type === AwardType.MATCHUP_BASED && !criteriaData.margin_type) {
      newErrors.margin_type = 'Margin type is required for matchup awards'
    }
    
    if (criteriaData.type === AwardType.CUSTOM && !criteriaData.custom_description) {
      newErrors.custom_description = 'Custom description is required for custom awards'
    }
    
    if (criteriaData.threshold && isNaN(Number(criteriaData.threshold))) {
      newErrors.threshold = 'Threshold must be a valid number'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return
    if (!leagueId && !award?.league_id) {
      setErrors({ general: 'League ID is required' })
      return
    }
    
    try {
      const criteria: AwardCriteria = {
        type: criteriaData.type,
        ...(criteriaData.stat_category && { stat_category: criteriaData.stat_category }),
        ...(criteriaData.comparison && { comparison: criteriaData.comparison }),
        ...(criteriaData.threshold && { threshold: Number(criteriaData.threshold) }),
        ...(criteriaData.margin_type && { margin_type: criteriaData.margin_type }),
        ...(criteriaData.custom_formula && { custom_formula: criteriaData.custom_formula }),
        ...(criteriaData.custom_description && { custom_description: criteriaData.custom_description }),
        metadata: {}
      }
      
      if (isEditing) {
        const updateData: AwardUpdateRequest = {
          name: formData.name,
          description: formData.description,
          emoji: formData.emoji,
          criteria,
          frequency: formData.frequency,
          is_public: formData.is_public,
          auto_assign: formData.auto_assign,
          color: formData.color
        }
        
        const updatedAward = await updateAward.mutateAsync({
          id: award.id,
          data: updateData
        })
        onSuccess?.(updatedAward)
      } else {
        const createData: AwardCreateRequest = {
          league_id: leagueId!,
          name: formData.name,
          description: formData.description,
          emoji: formData.emoji,
          criteria,
          frequency: formData.frequency,
          is_public: formData.is_public,
          auto_assign: formData.auto_assign,
          color: formData.color
        }
        
        const newAward = await createAward.mutateAsync(createData)
        onSuccess?.(newAward)
      }
    } catch (error) {
      setErrors({ 
        general: error instanceof Error ? error.message : 'Failed to save award' 
      })
    }
  }
  
  // Apply template
  const applyTemplate = useCallback((templateId: string) => {
    const template = templatesData?.templates.find(t => t.id === templateId)
    if (!template) return
    
    setFormData(prev => ({
      ...prev,
      name: template.name,
      description: template.description,
      emoji: template.emoji,
      frequency: template.frequency
    }))
    
    setCriteriaData({
      type: template.criteria.type,
      stat_category: template.criteria.stat_category || '',
      comparison: template.criteria.comparison || 'highest',
      threshold: template.criteria.threshold?.toString() || '',
      margin_type: template.criteria.margin_type || '',
      custom_formula: template.criteria.custom_formula || '',
      custom_description: template.criteria.custom_description || ''
    })
  }, [templatesData?.templates])
  
  // Handle template selection
  useEffect(() => {
    if (selectedTemplate) {
      applyTemplate(selectedTemplate)
    }
  }, [selectedTemplate, applyTemplate])
  
  const isLoading = createAward.isPending || updateAward.isPending
  
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          {isEditing ? 'Edit Award' : 'Create New Award'}
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          {isEditing 
            ? 'Update your custom award settings'
            : 'Create a custom award for your league'
          }
        </p>
      </div>
      
      {/* Template Selection */}
      {!isEditing && templatesData?.templates && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Use Template (Optional)
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Choose from popular awards...</option>
            {templatesData.categories.map(category => (
              <optgroup key={category} label={category}>
                {templatesData.templates
                  .filter(t => t.category === category)
                  .map(template => (
                    <option key={template.id} value={template.id}>
                      {template.emoji} {template.name}
                    </option>
                  ))
                }
              </optgroup>
            ))}
          </select>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Award Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Award Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., Highest Scorer, Biggest Upset"
              maxLength={100}
            />
            {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Emoji
            </label>
            <input
              type="text"
              value={formData.emoji}
              onChange={(e) => setFormData(prev => ({ ...prev, emoji: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="🏆"
              maxLength={10}
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Describe what this award is for..."
            maxLength={500}
          />
          {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description}</p>}
        </div>
        
        {/* Award Criteria */}
        <div className="border-t border-gray-200 dark:border-gray-600 pt-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Award Criteria
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Award Type *
              </label>
              <select
                value={criteriaData.type}
                onChange={(e) => setCriteriaData(prev => ({ 
                  ...prev, 
                  type: e.target.value as AwardType 
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={AwardType.TEAM_PERFORMANCE}>Team Performance</option>
                <option value={AwardType.PLAYER_PERFORMANCE}>Player Performance</option>
                <option value={AwardType.MATCHUP_BASED}>Matchup Based</option>
                <option value={AwardType.SEASON_LONG}>Season Long</option>
                <option value={AwardType.CUSTOM}>Custom</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Frequency
              </label>
              <select
                value={formData.frequency}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  frequency: e.target.value as AwardFrequency 
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={AwardFrequency.WEEKLY}>Weekly</option>
                <option value={AwardFrequency.MONTHLY}>Monthly</option>
                <option value={AwardFrequency.SEASON}>Season</option>
                <option value={AwardFrequency.PLAYOFF}>Playoff</option>
              </select>
            </div>
          </div>
          
          {/* Conditional Criteria Fields */}
          {(criteriaData.type === AwardType.TEAM_PERFORMANCE || 
            criteriaData.type === AwardType.PLAYER_PERFORMANCE) && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Stat Category *
                </label>
                <select
                  value={criteriaData.stat_category}
                  onChange={(e) => setCriteriaData(prev => ({ 
                    ...prev, 
                    stat_category: e.target.value 
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select stat...</option>
                  <option value="points_scored">Points Scored</option>
                  <option value="total_yards">Total Yards</option>
                  <option value="touchdowns">Touchdowns</option>
                  <option value="turnovers">Turnovers</option>
                  <option value="field_goals">Field Goals</option>
                  <option value="bench_points">Bench Points</option>
                </select>
                {errors.stat_category && <p className="text-red-500 text-sm mt-1">{errors.stat_category}</p>}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Comparison *
                </label>
                <select
                  value={criteriaData.comparison}
                  onChange={(e) => setCriteriaData(prev => ({ 
                    ...prev, 
                    comparison: e.target.value 
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="highest">Highest</option>
                  <option value="lowest">Lowest</option>
                  <option value="closest_to">Closest To</option>
                </select>
                {errors.comparison && <p className="text-red-500 text-sm mt-1">{errors.comparison}</p>}
              </div>
              
              {criteriaData.comparison === 'closest_to' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Target Value
                  </label>
                  <input
                    type="number"
                    value={criteriaData.threshold}
                    onChange={(e) => setCriteriaData(prev => ({ 
                      ...prev, 
                      threshold: e.target.value 
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                             focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="100"
                  />
                  {errors.threshold && <p className="text-red-500 text-sm mt-1">{errors.threshold}</p>}
                </div>
              )}
            </div>
          )}
          
          {criteriaData.type === AwardType.MATCHUP_BASED && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Margin Type *
              </label>
              <select
                value={criteriaData.margin_type}
                onChange={(e) => setCriteriaData(prev => ({ 
                  ...prev, 
                  margin_type: e.target.value 
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select margin type...</option>
                <option value="closest">Closest Game</option>
                <option value="biggest_blowout">Biggest Blowout</option>
                <option value="upset">Biggest Upset</option>
              </select>
              {errors.margin_type && <p className="text-red-500 text-sm mt-1">{errors.margin_type}</p>}
            </div>
          )}
          
          {criteriaData.type === AwardType.CUSTOM && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Custom Description *
              </label>
              <textarea
                value={criteriaData.custom_description}
                onChange={(e) => setCriteriaData(prev => ({ 
                  ...prev, 
                  custom_description: e.target.value 
                }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe the custom criteria for this award..."
              />
              {errors.custom_description && <p className="text-red-500 text-sm mt-1">{errors.custom_description}</p>}
            </div>
          )}
        </div>
        
        {/* Advanced Settings */}
        <div className="border-t border-gray-200 dark:border-gray-600 pt-6">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500"
          >
            <span>{showAdvanced ? 'Hide' : 'Show'} Advanced Settings</span>
            <svg
              className={`ml-1 h-4 w-4 transform transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showAdvanced && (
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_public}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        is_public: e.target.checked 
                      }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Public Award (visible to all league members)
                    </span>
                  </label>
                </div>
                
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.auto_assign}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        auto_assign: e.target.checked 
                      }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Auto-assign based on criteria
                    </span>
                  </label>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Award Color
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="color"
                    value={formData.color}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      color: e.target.value 
                    }))}
                    className="h-10 w-16 border border-gray-300 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={formData.color}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      color: e.target.value 
                    }))}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                             focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="#fbbf24"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Error Display */}
        {errors.general && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
            <p className="text-red-600 dark:text-red-400 text-sm">{errors.general}</p>
          </div>
        )}
        
        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200 dark:border-gray-600">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 
                       bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 
                       rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            >
              Cancel
            </button>
          )}
          
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 
                     border border-transparent rounded-md hover:bg-blue-700 
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                     disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center space-x-2"
          >
            {isLoading && (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            )}
            <span>{isEditing ? 'Update Award' : 'Create Award'}</span>
          </button>
        </div>
      </form>
    </div>
  )
}
