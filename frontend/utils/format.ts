function parseServerDate(dateStr: string): Date {
  const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(dateStr)
  return new Date(hasTimezone ? dateStr : `${dateStr}Z`)
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function formatDate(dateStr: string): string {
  return parseServerDate(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatRelative(dateStr: string): string {
  const diff = Date.now() - parseServerDate(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return formatDate(dateStr)
}

export function fileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const map: Record<string, string> = {
    sh: 'mdi:console', bash: 'mdi:console', zsh: 'mdi:console',
    py: 'mdi:language-python', js: 'mdi:language-javascript', ts: 'mdi:language-typescript',
    json: 'mdi:code-json', yaml: 'mdi:file-code', yml: 'mdi:file-code',
    md: 'mdi:language-markdown', txt: 'mdi:file-document-outline',
    zip: 'mdi:folder-zip', tar: 'mdi:folder-zip', gz: 'mdi:folder-zip',
    apk: 'mdi:android', pdf: 'mdi:file-pdf-box',
    png: 'mdi:file-image', jpg: 'mdi:file-image', jpeg: 'mdi:file-image',
  }
  return map[ext || ''] || 'mdi:file-outline'
}
