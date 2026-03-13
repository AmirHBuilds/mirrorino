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
  icon: string
  boxClass: string
}

const platformMeta: Record<MirrorPlatform, MirrorPlatformMeta> = {
  github: { key: 'github', label: 'GitHub', icon: 'mirror-platforms:github', boxClass: 'border-white/15 bg-black/35' },
  gitlab: { key: 'gitlab', label: 'GitLab', icon: 'mirror-platforms:gitlab', boxClass: 'border-orange-400/30 bg-orange-500/10' },
  bitbucket: { key: 'bitbucket', label: 'Bitbucket', icon: 'mirror-platforms:bitbucket', boxClass: 'border-blue-400/30 bg-blue-500/10' },
  codeberg: { key: 'codeberg', label: 'Codeberg', icon: 'mirror-platforms:codeberg', boxClass: 'border-cyan-400/30 bg-cyan-500/10' },
  sourcehut: { key: 'sourcehut', label: 'SourceHut', icon: 'mirror-platforms:sourcehut', boxClass: 'border-emerald-400/30 bg-emerald-500/10' },
  other: { key: 'other', label: 'External', icon: 'mirror-platforms:other', boxClass: 'border-border bg-surface-2/35' },
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
      displayPath: normalizedUrl.length > 58 ? `${normalizedUrl.slice(0, 55)}...` : normalizedUrl,
      normalizedUrl,
      isValid: false,
    }
  }
}
