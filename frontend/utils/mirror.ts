export interface MirrorInfo {
  platform: MirrorPlatform
  owner: string
  repo: string
  displayPath: string
  normalizedUrl: string
  isValid: boolean
}

export type MirrorPlatform = 'github' | 'gitlab' | 'bitbucket' | 'codeberg' | 'sourcehut' | 'other'

export interface MirrorPlatformMeta {
  key: MirrorPlatform
  label: string
  iconPath: string
  boxClass: string
}

const platformMeta: Record<MirrorPlatform, MirrorPlatformMeta> = {
  github: { key: 'github', label: 'GitHub', iconPath: '/icons/platforms/github.svg', boxClass: 'border-white/20 bg-black/45' },
  gitlab: { key: 'gitlab', label: 'GitLab', iconPath: '/icons/platforms/gitlab.svg', boxClass: 'border-orange-400/30 bg-orange-500/10' },
  bitbucket: { key: 'bitbucket', label: 'Bitbucket', iconPath: '/icons/platforms/bitbucket.svg', boxClass: 'border-blue-400/30 bg-blue-500/10' },
  codeberg: { key: 'codeberg', label: 'Codeberg', iconPath: '/icons/platforms/codeberg.svg', boxClass: 'border-cyan-400/30 bg-cyan-500/10' },
  sourcehut: { key: 'sourcehut', label: 'SourceHut', iconPath: '/icons/platforms/sourcehut.svg', boxClass: 'border-emerald-400/30 bg-emerald-500/10' },
  other: { key: 'other', label: 'External source', iconPath: '/icons/platforms/other.svg', boxClass: 'border-border bg-surface-2/40' },
}

const patterns: Array<{ platform: MirrorPlatform; matcher: RegExp }> = [
  { platform: 'github', matcher: /(^|\.)github\.com$/i },
  { platform: 'gitlab', matcher: /(^|\.)gitlab\.com$/i },
  { platform: 'bitbucket', matcher: /(^|\.)bitbucket\.org$/i },
  { platform: 'codeberg', matcher: /(^|\.)codeberg\.org$/i },
  { platform: 'sourcehut', matcher: /(^|\.)sr\.ht$/i },
]

export function detectMirrorPlatform(hostname: string): MirrorPlatform {
  for (const item of patterns) {
    if (item.matcher.test(hostname)) return item.platform
  }
  return 'other'
}

export function getMirrorPlatformMeta(platform: MirrorPlatform): MirrorPlatformMeta {
  return platformMeta[platform]
}

export function parseMirrorUrl(url: string | null | undefined): MirrorInfo | null {
  if (!url) return null
  const normalizedUrl = url.trim()
  if (!normalizedUrl) return null

  try {
    const parsed = new URL(normalizedUrl)
    const isValid = /^https?:$/i.test(parsed.protocol)
    const platform = detectMirrorPlatform(parsed.hostname)
    const segments = parsed.pathname.split('/').filter(Boolean)

    let owner = ''
    let repo = ''

    if (segments.length >= 2) {
      owner = segments[0]
      repo = segments[1].replace(/\.git$/i, '')
    }

    const displayPath = owner && repo
      ? `${owner}/${repo}`
      : `${parsed.hostname}${parsed.pathname}`.replace(/\/$/, '')

    return { platform, owner, repo, displayPath, normalizedUrl, isValid }
  } catch {
    return {
      platform: 'other',
      owner: '',
      repo: '',
      displayPath: normalizedUrl.length > 72 ? `${normalizedUrl.slice(0, 69)}...` : normalizedUrl,
      normalizedUrl,
      isValid: false,
    }
  }
}
