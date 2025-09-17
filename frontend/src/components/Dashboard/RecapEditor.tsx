import React, { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useUpdateRecap, useCreateRecap } from '../../hooks/useDashboardData'
import { Recap } from '../../types/api'
import RecapEditor from '../RecapEditor/RecapEditor'

interface RecapEditorPageProps {
  recap?: Recap
}

const RecapEditorPage: React.FC<RecapEditorPageProps> = ({ recap }) => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const recapId = searchParams.get('id')
  const isEditMode = Boolean(recapId && recap)

  const { mutate: updateRecap } = useUpdateRecap()
  const { mutate: createRecap } = useCreateRecap()

  const handleSave = async (content: string, title: string) => {
    try {
      if (isEditMode && recap) {
        // Update existing recap
        await updateRecap(`/recaps/${recap.id}`, {
          title,
          content,
          status: 'completed'
        })
      } else {
        // Create new recap
        await createRecap('/recaps', {
          title,
          content,
          // Default values for new recaps
          league_id: searchParams.get('league_id') || '',
          week: parseInt(searchParams.get('week') || '1'),
          season: parseInt(searchParams.get('season') || new Date().getFullYear().toString()),
          tone: 'humorous',
          length: 'medium',
          status: 'completed',
          include_awards: true,
          include_predictions: true,
          focus_on_user_team: false
        })
      }
      
      // Navigate back to dashboard or recap view
      navigate('/dashboard?tab=recaps')
    } catch (error) {
      console.error('Failed to save recap:', error)
      throw error
    }
  }

  const handleCancel = () => {
    navigate('/dashboard?tab=recaps')
  }

  return (
    <div className="h-screen overflow-hidden">
      <RecapEditor
        recap={recap}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    </div>
  )
}

export default RecapEditorPage