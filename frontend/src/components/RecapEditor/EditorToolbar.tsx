import React, { useCallback, useEffect, useState } from 'react'
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext'
import {
  $getSelection,
  $isRangeSelection,
  FORMAT_TEXT_COMMAND,
  SELECTION_CHANGE_COMMAND,
  COMMAND_PRIORITY_CRITICAL,
} from 'lexical'
import {
  $createHeadingNode,
  $createQuoteNode,
  $isHeadingNode,
  HeadingTagType,
} from '@lexical/rich-text'
import {
  INSERT_ORDERED_LIST_COMMAND,
  INSERT_UNORDERED_LIST_COMMAND,
  REMOVE_LIST_COMMAND,
  $isListNode,
} from '@lexical/list'
import { $setBlocksType } from '@lexical/selection'
import { $createParagraphNode, $getRoot } from 'lexical'

const SUPPORTED_URL_PROTOCOLS = new Set([
  'http:',
  'https:',
  'mailto:',
  'sms:',
  'tel:',
])

const EditorToolbar: React.FC = () => {
  const [editor] = useLexicalComposerContext()
  const [isBold, setIsBold] = useState(false)
  const [isItalic, setIsItalic] = useState(false)
  const [isUnderline, setIsUnderline] = useState(false)
  const [isStrikethrough, setIsStrikethrough] = useState(false)
  const [blockType, setBlockType] = useState('paragraph')

  const updateToolbar = useCallback(() => {
    const selection = $getSelection()
    if ($isRangeSelection(selection)) {
      setIsBold(selection.hasFormat('bold'))
      setIsItalic(selection.hasFormat('italic'))
      setIsUnderline(selection.hasFormat('underline'))
      setIsStrikethrough(selection.hasFormat('strikethrough'))

      const anchorNode = selection.anchor.getNode()
      const element =
        anchorNode.getKey() === 'root'
          ? anchorNode
          : anchorNode.getTopLevelElementOrThrow()

      const elementKey = element.getKey()
      const elementDOM = editor.getElementByKey(elementKey)

      if (elementDOM !== null) {
        if ($isListNode(element)) {
          const parentList = element
          const type = parentList.getListType()
          setBlockType(type)
        } else {
          const type = $isHeadingNode(element)
            ? element.getTag()
            : element.getType()
          setBlockType(type)
        }
      }
    }
  }, [editor])

  useEffect(() => {
    return editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        updateToolbar()
      })
    })
  }, [editor, updateToolbar])

  useEffect(() => {
    return editor.registerCommand(
      SELECTION_CHANGE_COMMAND,
      () => {
        updateToolbar()
        return false
      },
      COMMAND_PRIORITY_CRITICAL
    )
  }, [editor, updateToolbar])

  const formatText = (format: 'bold' | 'italic' | 'underline' | 'strikethrough') => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, format)
  }

  const formatParagraph = () => {
    if (blockType !== 'paragraph') {
      editor.update(() => {
        const selection = $getSelection()
        if ($isRangeSelection(selection)) {
          $setBlocksType(selection, () => $createParagraphNode())
        }
      })
    }
  }

  const formatHeading = (headingSize: HeadingTagType) => {
    if (blockType !== headingSize) {
      editor.update(() => {
        const selection = $getSelection()
        if ($isRangeSelection(selection)) {
          $setBlocksType(selection, () => $createHeadingNode(headingSize))
        }
      })
    }
  }

  const formatBulletList = () => {
    if (blockType !== 'bullet') {
      editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined)
    } else {
      editor.dispatchCommand(REMOVE_LIST_COMMAND, undefined)
    }
  }

  const formatNumberedList = () => {
    if (blockType !== 'number') {
      editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined)
    } else {
      editor.dispatchCommand(REMOVE_LIST_COMMAND, undefined)
    }
  }

  const formatQuote = () => {
    if (blockType !== 'quote') {
      editor.update(() => {
        const selection = $getSelection()
        if ($isRangeSelection(selection)) {
          $setBlocksType(selection, () => $createQuoteNode())
        }
      })
    }
  }

  const blockTypeToBlockName = {
    bullet: 'Bulleted List',
    code: 'Code Block',
    h1: 'Heading 1',
    h2: 'Heading 2',
    h3: 'Heading 3',
    h4: 'Heading 4',
    h5: 'Heading 5',
    h6: 'Heading 6',
    number: 'Numbered List',
    paragraph: 'Normal',
    quote: 'Quote',
  }

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 py-2">
      <div className="flex items-center space-x-1">
        {/* Block Type Selector */}
        <select
          className="mr-2 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          value={blockType}
          onChange={(e) => {
            const value = e.target.value
            if (value === 'paragraph') {
              formatParagraph()
            } else if (value === 'h1' || value === 'h2' || value === 'h3') {
              formatHeading(value as HeadingTagType)
            } else if (value === 'bullet') {
              formatBulletList()
            } else if (value === 'number') {
              formatNumberedList()
            } else if (value === 'quote') {
              formatQuote()
            }
          }}
        >
          <option value="paragraph">Normal</option>
          <option value="h1">Heading 1</option>
          <option value="h2">Heading 2</option>
          <option value="h3">Heading 3</option>
          <option value="quote">Quote</option>
          <option value="bullet">Bullet List</option>
          <option value="number">Numbered List</option>
        </select>

        {/* Formatting Buttons */}
        <button
          className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-600 ${
            isBold
              ? 'bg-gray-200 dark:bg-gray-600 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-300'
          }`}
          onClick={() => formatText('bold')}
          title="Bold"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M4 2a1 1 0 011-1h5.5a3.5 3.5 0 010 7H6v2h4.5a3.5 3.5 0 010 7H5a1 1 0 01-1-1V2zm2 6h4.5a1.5 1.5 0 000-3H6v3zm0 2v3h4.5a1.5 1.5 0 000-3H6z" />
          </svg>
        </button>

        <button
          className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-600 ${
            isItalic
              ? 'bg-gray-200 dark:bg-gray-600 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-300'
          }`}
          onClick={() => formatText('italic')}
          title="Italic"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M8 1a1 1 0 000 2h1.5l-3 14H5a1 1 0 000 2h6a1 1 0 000-2H9.5l3-14H14a1 1 0 000-2H8z" />
          </svg>
        </button>

        <button
          className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-600 ${
            isUnderline
              ? 'bg-gray-200 dark:bg-gray-600 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-300'
          }`}
          onClick={() => formatText('underline')}
          title="Underline"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M4 18a1 1 0 001 1h10a1 1 0 100-2H5a1 1 0 00-1 1zM3 7a7 7 0 1114 0v3a1 1 0 11-2 0V7A5 5 0 005 7v3a1 1 0 11-2 0V7z" />
          </svg>
        </button>

        <button
          className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-600 ${
            isStrikethrough
              ? 'bg-gray-200 dark:bg-gray-600 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-300'
          }`}
          onClick={() => formatText('strikethrough')}
          title="Strikethrough"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6 4a4 4 0 014-4c1.268 0 2.39.63 3.068 1.593a1 1 0 11-1.736 1.014A2 2 0 0010 2a2 2 0 00-2 2v1h2a1 1 0 110 2H6V4zm4 8v3a2 2 0 104 0 1 1 0 112 0 4 4 0 01-8 0v-3h2z" clipRule="evenodd" />
          </svg>
        </button>

        {/* Separator */}
        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-2"></div>

        {/* List Buttons */}
        <button
          className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-600 ${
            blockType === 'bullet'
              ? 'bg-gray-200 dark:bg-gray-600 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-300'
          }`}
          onClick={formatBulletList}
          title="Bullet List"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        </button>

        <button
          className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-600 ${
            blockType === 'number'
              ? 'bg-gray-200 dark:bg-gray-600 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-300'
          }`}
          onClick={formatNumberedList}
          title="Numbered List"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 4a1 1 0 000 2h.5v.5a.5.5 0 001 0V6H5a1 1 0 100-2H3zM3 13a1 1 0 100 2h.5v.5a.5.5 0 001 0V15H5a1 1 0 100-2H3zM2.5 8.5a.5.5 0 01.5-.5h1a.5.5 0 010 1H3.5v.5a.5.5 0 01-1 0v-1zM8 4a1 1 0 000 2h9a1 1 0 100-2H8zM7 9a1 1 0 011-1h9a1 1 0 110 2H8a1 1 0 01-1-1zM8 13a1 1 0 100 2h9a1 1 0 100-2H8z" clipRule="evenodd" />
          </svg>
        </button>

        <button
          className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-600 ${
            blockType === 'quote'
              ? 'bg-gray-200 dark:bg-gray-600 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-300'
          }`}
          onClick={formatQuote}
          title="Quote"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.75 2.5a.75.75 0 00-.75.75v12a.75.75 0 001.5 0V15h7.5a.75.75 0 00.75-.75v-9a.75.75 0 00-.75-.75H6.5v-.5a.75.75 0 00-.75-.75zm.75 2h6.5v7.5h-6.5V4.5z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default EditorToolbar