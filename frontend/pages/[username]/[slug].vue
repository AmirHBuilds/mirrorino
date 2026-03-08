<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <div v-if="pending" class="animate-pulse space-y-4">
      <div class="h-8 bg-surface-2 rounded w-64"></div>
      <div class="h-4 bg-surface-2 rounded w-96"></div>
      <div class="card h-48"></div>
    </div>
    <template v-else-if="repo">
      <div v-if="displayStatus === 'rejected'" class="flex items-start gap-3 bg-danger/5 border border-danger/30 rounded-lg px-4 py-3 mb-6 text-sm text-danger">
        <Icon name="mdi:alert-circle" class="w-5 h-5 shrink-0 mt-0.5" />
        <span><strong>Marked as spam.</strong> This repository was rejected during verification.</span>
      </div>
      <div v-else-if="displayStatus === 'unverified'" class="flex items-start gap-3 bg-warning/5 border border-warning/30 rounded-lg px-4 py-3 mb-6 text-sm text-warning">
        <Icon name="mdi:alert" class="w-5 h-5 shrink-0 mt-0.5" />
        <span><strong>Unverified repository.</strong> Not reviewed by admins. Download at your own risk.</span>
      </div>

      <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-6">
        <div>
          <div class="flex flex-wrap items-center gap-2 text-sm mb-2">
            <Icon name="mdi:source-repository" class="w-4 h-4 text-muted" />
            <NuxtLink :to="`/${repo.owner.username}/repos`" class="text-muted hover:underline">{{ repo.owner.username }}</NuxtLink>
            <span class="text-muted">/</span>
            <span class="font-semibold">{{ repo.name }}</span>
            <VerificationBadge :status="displayStatus" />
            <span class="text-xs px-1.5 py-0.5 rounded border border-border font-mono text-muted">
              {{ repo.is_public ? 'Public' : 'Private' }}
            </span>
          </div>
          <p v-if="repo.description" class="text-sm text-muted">{{ repo.description }}</p>
        </div>
        <div class="flex items-center gap-2 shrink-0" v-if="isOwner">
          <button v-if="repo.verification_status === 'unverified'" @click="requestVerify" class="btn-secondary text-sm py-1.5">
            <Icon name="mdi:shield-check-outline" class="w-4 h-4" /> Request Verification
          </button>
          <NuxtLink :to="`/user/repos/${repo.owner.username}/${repo.slug}/upload`" class="btn-primary text-sm py-1.5">
            <Icon name="mdi:upload" class="w-4 h-4" /> Upload files
          </NuxtLink>
        </div>
      </div>

      <div class="flex flex-wrap gap-5 text-xs text-muted font-mono mb-6 border-b border-border pb-4">
        <span class="flex items-center gap-1.5"><Icon name="mdi:file-multiple-outline" class="w-4 h-4" />{{ repo.file_count }} files</span>
        <span class="flex items-center gap-1.5"><Icon name="mdi:download-outline" class="w-4 h-4" />{{ repo.download_count.toLocaleString() }}</span>
        <span class="flex items-center gap-1.5"><Icon name="mdi:database-outline" class="w-4 h-4" />{{ formatBytes(repo.total_size) }}</span>
        <span class="ml-auto flex items-center gap-1.5"><Icon name="mdi:clock-outline" class="w-4 h-4" />{{ formatRelative(repo.updated_at) }}</span>
      </div>

      <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b border-border flex items-center justify-between">
          <span class="text-sm font-semibold">Files</span>
          <span class="text-xs text-muted font-mono">{{ files?.length || 0 }} files</span>
        </div>
        <div v-if="!files?.length" class="py-16 text-center text-muted">
          <Icon name="mdi:folder-open-outline" class="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p class="text-sm">No files uploaded yet</p>
        </div>
        <div v-else class="divide-y divide-border">
          <FileRow
            v-for="file in files"
            :key="file.id"
            :file="file"
            :repo-username="repo.owner.username"
            :repo-slug="repo.slug"
            :can-delete="isOwner"
            @delete="onDeleteFile"
          />
        </div>
      </div>

      <div v-if="readmeContent" class="card p-4 mt-6">
        <p class="text-xs text-muted font-mono uppercase tracking-wider mb-3">README.md</p>
        <div class="markdown-body" v-html="readmeHtml"></div>
      </div>
    </template>
    <div v-else class="text-center py-24 text-muted">Repository not found</div>
  </div>
</template>

<script setup lang="ts">
import { formatBytes, formatRelative } from '~/utils/format'
import type { Repo, RepoFile } from '~/types'
import { visibleVerificationStatus } from '~/utils/repo'

const route = useRoute()
const { get, post, delete: del } = useApi()
const apiBase = useRuntimeConfig().public.apiBase
const { user, isLoggedIn } = useAuth()

const { data: repo, pending, refresh: refreshRepo } = await useAsyncData(
  () => `repo-detail:${route.params.username}:${route.params.slug}`,
  async () => {
    try {
      return await get<Repo>(`/api/repos/users/${route.params.username}/${route.params.slug}`)
    } catch {
      return null
    }
  },
  { server: false, default: () => null },
)

const { data: files, refresh: refreshFiles } = await useAsyncData(
  () => `repo-files:${repo.value?.owner.username || route.params.username}:${repo.value?.slug || route.params.slug}`,
  async () => {
    if (!repo.value) return []
    return get<RepoFile[]>(`/api/users/${repo.value.owner.username}/repos/${repo.value.slug}/files`)
  },
  { watch: [repo], server: false, default: () => [] },
)

const isOwner = computed(() => isLoggedIn.value && !!repo.value && user.value?.id === repo.value.owner.id)
const displayStatus = computed(() => repo.value ? visibleVerificationStatus(repo.value.verification_status, !!isOwner.value) : 'unverified')

const readmeFile = computed(() => files.value?.find((file) => file.original_name.toLowerCase() === 'readme.md') ?? null)

const { data: readmeContent } = await useAsyncData(
  () => `repo-readme:${repo.value?.owner.username || route.params.username}:${repo.value?.slug || route.params.slug}:${readmeFile.value?.id || 0}`,
  async () => {
    if (!repo.value || !readmeFile.value) return null
    const res = await fetch(`${apiBase}/raw/${repo.value.owner.username}/${repo.value.slug}/${encodeURIComponent(readmeFile.value.original_name)}`)
    if (!res.ok) return null
    return await res.text()
  },
  { watch: [repo, readmeFile], server: false, default: () => null },
)

function escapeHtml(content: string) {
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function markdownToHtml(content: string) {
  const escaped = escapeHtml(content)
  const lines = escaped.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let inCode = false
  let listType: 'ul' | 'ol' | null = null

  const closeList = () => {
    if (listType) {
      html.push(`</${listType}>`)
      listType = null
    }
  }

  const inline = (line: string) => line
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')

  for (const rawLine of lines) {
    const line = rawLine.trimEnd()

    if (line.startsWith('```')) {
      closeList()
      html.push(inCode ? '</code></pre>' : '<pre><code>')
      inCode = !inCode
      continue
    }

    if (inCode) {
      html.push(`${line}\n`)
      continue
    }

    if (!line.trim()) {
      closeList()
      continue
    }

    if (line.startsWith('### ')) { closeList(); html.push(`<h3>${inline(line.slice(4))}</h3>`); continue }
    if (line.startsWith('## ')) { closeList(); html.push(`<h2>${inline(line.slice(3))}</h2>`); continue }
    if (line.startsWith('# ')) { closeList(); html.push(`<h1>${inline(line.slice(2))}</h1>`); continue }
    if (line.startsWith('> ')) { closeList(); html.push(`<blockquote>${inline(line.slice(2))}</blockquote>`); continue }
    if (/^-{3,}$/.test(line) || /^\*{3,}$/.test(line)) { closeList(); html.push('<hr>'); continue }

    const unorderedMatch = line.match(/^[-*]\s+(.+)$/)
    if (unorderedMatch) {
      if (listType !== 'ul') {
        closeList()
        html.push('<ul>')
        listType = 'ul'
      }
      html.push(`<li>${inline(unorderedMatch[1])}</li>`)
      continue
    }

    const orderedMatch = line.match(/^\d+\.\s+(.+)$/)
    if (orderedMatch) {
      if (listType !== 'ol') {
        closeList()
        html.push('<ol>')
        listType = 'ol'
      }
      html.push(`<li>${inline(orderedMatch[1])}</li>`)
      continue
    }

    closeList()
    html.push(`<p>${inline(line)}</p>`)
  }

  closeList()
  if (inCode) html.push('</code></pre>')
  return html.join('')
}

const readmeHtml = computed(() => (readmeContent.value ? markdownToHtml(readmeContent.value) : ''))

async function requestVerify() {
  try {
    await post(`/api/repos/${repo.value?.id}/request-verification`, {})
  } catch {}
  await refreshRepo()
}

async function onDeleteFile(id: number) {
  await del(`/api/files/${id}`)
  await refreshFiles()
}

useSeoMeta({ title: computed(() => `${route.params.username}/${route.params.slug}`) })
</script>
