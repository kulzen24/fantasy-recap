import React, { useState, useCallback, useEffect } from 'react'
import { LexicalComposer } from '@lexical/react/LexicalComposer'
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin'
import { ContentEditable } from '@lexical/react/LexicalContentEditable'
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin'
import { LexicalErrorBoundary } from '@lexical/react/LexicalErrorBoundary'
import { $getRoot, $getSelection } from 'lexical'
import { $createHeadingNode, $createQuoteNode } from '@lexical/rich-text'
import { $createListNode, $createListItemNode } from '@lexical/list'
import { ListPlugin } from '@lexical/react/LexicalListPlugin'
import { LinkPlugin } from '@lexical/react/LexicalLinkPlugin'
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext'
import { $generateHtmlFromNodes } from '@lexical/html'

import { Recap } from '../../types/api'
import EditorToolbar from './EditorToolbar'
import { editorConfig } from './editorConfig'
import { RecapExporter, sanitizeFilename } from './exportUtils'
import './RecapEditor.css'

interface RecapEditorProps {
  recap?: Recap
  onSave: (content: string, title: string) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

const RecapEditor: React.FC<RecapEditorProps> = ({
  recap,
  onSave,
  onCancel,
  isLoading = false
}) => {
  const [title, setTitle] = useState(recap?.title || '')
  const [isSaving, setIsSaving] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [editorState, setEditorState] = useState<string>('')
  const [htmlContent, setHtmlContent] = useState<string>('')
  const [showExportMenu, setShowExportMenu] = useState(false)

  // Auto-save functionality
  const [autoSaveTimeout, setAutoSaveTimeout] = useState<NodeJS.Timeout | null>(null)
  
  // Export functionality
  const [exporter, setExporter] = useState<RecapExporter | null>(null)

  const handleAutoSave = useCallback(async () => {
    if (hasUnsavedChanges && !isSaving && title.trim() && editorState.trim()) {
      setIsSaving(true)
      try {
        await onSave(editorState, title)
        setHasUnsavedChanges(false)
      } catch (error) {
        console.error('Auto-save failed:', error)
      } finally {
        setIsSaving(false)
      }
    }
  }, [hasUnsavedChanges, isSaving, title, editorState, onSave])

  // Trigger auto-save after 2 seconds of inactivity
  useEffect(() => {
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout)
    }
    
    if (hasUnsavedChanges) {
      const timeout = setTimeout(handleAutoSave, 2000)
      setAutoSaveTimeout(timeout)
    }

    return () => {
      if (autoSaveTimeout) {
        clearTimeout(autoSaveTimeout)
      }
    }
  }, [hasUnsavedChanges, handleAutoSave, autoSaveTimeout])

  const handleSave = async () => {
    if (!title.trim()) {
      alert('Please enter a title for the recap')
      return
    }

    setIsSaving(true)
    try {
      await onSave(editorState, title)
      setHasUnsavedChanges(false)
    } catch (error) {
      console.error('Save failed:', error)
      alert('Failed to save recap. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTitle(e.target.value)
    setHasUnsavedChanges(true)
  }

  // Handle editor state changes
  const EditorStateChangeHandler = () => {
    const [editor] = useLexicalComposerContext()
    
    useEffect(() => {
      // Set up exporter when editor is ready
      if (!exporter) {
        setExporter(new RecapExporter(editor))
      }
    }, [editor, exporter])
    
    useEffect(() => {
      return editor.registerUpdateListener(({ editorState }) => {
        editorState.read(() => {
          const root = $getRoot()
          const textContent = root.getTextContent()
          const htmlContent = $generateHtmlFromNodes(editor, null)
          
          setEditorState(textContent)
          setHtmlContent(htmlContent)
          setHasUnsavedChanges(true)
        })
      })
    }, [editor])

    return null
  }

  // Export handlers
  const handleExport = async (format: 'html' | 'markdown' | 'text') => {
    if (!exporter) return
    
    const filename = sanitizeFilename(title || 'recap')
    await exporter.exportAndDownload(
      { format, title, includeTitle: true },
      filename
    )
    setShowExportMenu(false)
  }

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showExportMenu) {
        setShowExportMenu(false)
      }
    }

    if (showExportMenu) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showExportMenu])

  // Warn user about unsaved changes before leaving
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasUnsavedChanges])

  // Initialize editor with existing recap content
  useEffect(() => {
    if (recap?.content && editorState === '') {
      setEditorState(recap.content)
      setHasUnsavedChanges(false)
    }
  }, [recap, editorState])

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex-1 mr-4">
            <input
              type="text"
              value={title}
              onChange={handleTitleChange}
              placeholder="Enter recap title..."
              className="w-full text-2xl font-bold bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              disabled={isLoading}
            />
          </div>
          
          <div className="flex items-center space-x-3">
            {/* Auto-save indicator */}
            {isSaving && (
              <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                <div className="animate-spin -ml-1 mr-2 h-4 w-4 border-2 border-gray-300 rounded-full border-t-transparent"></div>
                Saving...
              </div>
            )}
            
            {hasUnsavedChanges && !isSaving && (
              <span className="text-sm text-amber-600 dark:text-amber-400">
                Unsaved changes
              </span>
            )}
            
            {!hasUnsavedChanges && !isSaving && title && editorState && (
              <span className="text-sm text-green-600 dark:text-green-400">
                Saved
              </span>
            )}

            {/* Export Menu */}
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                disabled={isLoading || !title.trim() || !editorState.trim()}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                <svg className="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export
              </button>
              
              {showExportMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-10">
                  <div className="py-1">
                    <button
                      onClick={() => handleExport('html')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Export as HTML
                    </button>
                    <button
                      onClick={() => handleExport('markdown')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Export as Markdown
                    </button>
                    <button
                      onClick={() => handleExport('text')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Export as Text
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={onCancel}
              disabled={isLoading || isSaving}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              Cancel
            </button>
            
            <button
              onClick={handleSave}
              disabled={isLoading || isSaving || !title.trim() || !editorState.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <LexicalComposer initialConfig={editorConfig}>
          <EditorToolbar />
          
          <div className="flex-1 relative overflow-auto">
            <RichTextPlugin
              contentEditable={
                <ContentEditable 
                  className="h-full p-6 outline-none text-gray-900 dark:text-white"
                  style={{ minHeight: '100%' }}
                />
              }
              placeholder={
                <div className="absolute top-6 left-6 text-gray-400 dark:text-gray-500 pointer-events-none">
                  Start writing your recap...
                </div>
              }
              ErrorBoundary={LexicalErrorBoundary}
            />
          </div>
          
          <HistoryPlugin />
          <ListPlugin />
          <LinkPlugin />
          <EditorStateChangeHandler />
        </LexicalComposer>
      </div>
    </div>
  )
}

export default RecapEditor