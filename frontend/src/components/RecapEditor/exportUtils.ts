import { $getRoot } from 'lexical'
import { $generateHtmlFromNodes } from '@lexical/html'
import { LexicalEditor } from 'lexical'

export interface ExportOptions {
  format: 'html' | 'markdown' | 'text'
  title?: string
  includeTitle?: boolean
}

export class RecapExporter {
  private editor: LexicalEditor

  constructor(editor: LexicalEditor) {
    this.editor = editor
  }

  async exportAsHTML(options: ExportOptions = { format: 'html' }): Promise<string> {
    return new Promise((resolve) => {
      this.editor.getEditorState().read(() => {
        const htmlString = $generateHtmlFromNodes(this.editor, null)
        
        if (options.includeTitle && options.title) {
          const titleHtml = `<h1>${options.title}</h1>\n`
          resolve(titleHtml + htmlString)
        } else {
          resolve(htmlString)
        }
      })
    })
  }

  async exportAsText(options: ExportOptions = { format: 'text' }): Promise<string> {
    return new Promise((resolve) => {
      this.editor.getEditorState().read(() => {
        const root = $getRoot()
        const textContent = root.getTextContent()
        
        if (options.includeTitle && options.title) {
          resolve(`${options.title}\n\n${textContent}`)
        } else {
          resolve(textContent)
        }
      })
    })
  }

  async exportAsMarkdown(options: ExportOptions = { format: 'markdown' }): Promise<string> {
    // For now, we'll convert HTML to a basic markdown format
    // This could be enhanced with a proper HTML-to-Markdown converter
    const htmlContent = await this.exportAsHTML(options)
    
    let markdown = htmlContent
      // Convert headings
      .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n')
      .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n')
      .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n')
      .replace(/<h4[^>]*>(.*?)<\/h4>/gi, '#### $1\n')
      .replace(/<h5[^>]*>(.*?)<\/h5>/gi, '##### $1\n')
      .replace(/<h6[^>]*>(.*?)<\/h6>/gi, '###### $1\n')
      // Convert paragraphs
      .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
      // Convert bold and italic
      .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
      .replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**')
      .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
      .replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*')
      // Convert lists
      .replace(/<ul[^>]*>/gi, '')
      .replace(/<\/ul>/gi, '\n')
      .replace(/<ol[^>]*>/gi, '')
      .replace(/<\/ol>/gi, '\n')
      .replace(/<li[^>]*>(.*?)<\/li>/gi, '- $1\n')
      // Convert blockquotes
      .replace(/<blockquote[^>]*>(.*?)<\/blockquote>/gi, '> $1\n')
      // Convert links
      .replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)')
      // Remove remaining HTML tags
      .replace(/<[^>]*>/g, '')
      // Clean up multiple newlines
      .replace(/\n{3,}/g, '\n\n')
      .trim()

    return markdown
  }

  downloadFile(content: string, filename: string, mimeType: string = 'text/plain') {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  async exportAndDownload(options: ExportOptions, filename?: string) {
    const baseFilename = filename || 'recap'
    let content: string
    let mimeType: string
    let extension: string

    switch (options.format) {
      case 'html':
        content = await this.exportAsHTML(options)
        mimeType = 'text/html'
        extension = 'html'
        break
      case 'markdown':
        content = await this.exportAsMarkdown(options)
        mimeType = 'text/markdown'
        extension = 'md'
        break
      case 'text':
      default:
        content = await this.exportAsText(options)
        mimeType = 'text/plain'
        extension = 'txt'
        break
    }

    this.downloadFile(content, `${baseFilename}.${extension}`, mimeType)
  }
}

// Utility function to format title for filename
export const sanitizeFilename = (title: string): string => {
  return title
    .replace(/[^a-z0-9]/gi, '_')
    .replace(/_{2,}/g, '_')
    .replace(/^_|_$/g, '')
    .toLowerCase()
}