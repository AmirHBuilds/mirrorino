<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <div v-if="pending" class="animate-pulse space-y-4">
      <div class="h-8 bg-surface-2 rounded w-64"></div>
      <div class="h-4 bg-surface-2 rounded w-96"></div>
      <div class="card h-48"></div>
    </div>
    <template v-else-if="repo">
      <div v-if="repo.verification_status === 'unverified'" class="flex items-start gap-3 bg-warning/5 border border-warning/30 rounded-lg px-4 py-3 mb-6 text-sm text-warning">
        <Icon name="mdi:alert" class="w-5 h-5 shrink-0 mt-0.5" />
        <span><strong>Unverified repository.</strong> Not reviewed by admins. Download at your own risk.</span>
      </div>

      <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-6">
        <div>
          <div class="flex flex-wrap items-center gap-2 text-sm mb-2">
            <Icon name="mdi:source-repository" class="w-4 h-4 text-muted" />
            <span class="text-muted">{{ repo.owner.username }}</span>
            <span class="text-muted">/</span>
            <span class="font-semibold">{{ repo.name }}</span>
            <VerificationBadge :status="repo.verification_status" />
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

const route = useRoute()
const { get, post, delete: del } = useApi()
const apiBase = useRuntimeConfig().public.apiBase
const { user, isLoggedIn } = useAuth()

const { data: repo, pending, refresh: refreshRepo } = await useAsyncData('repo-detail', async () => {
  try {
    return await get<Repo>(`/api/repos/users/${route.params.username}/${route.params.slug}`)
  } catch {
    return null
  }
})

const { data: files, refresh: refreshFiles } = await useAsyncData('repo-files', async () => {
  if (!repo.value) return []
  return get<RepoFile[]>(`/api/users/${repo.value.owner.username}/repos/${repo.value.slug}/files`)
})

const isOwner = computed(() => isLoggedIn.value && !!repo.value && user.value?.id === repo.value.owner.id)

const readmeFile = computed(() => files.value?.find((file) => file.original_name.toLowerCase() === 'readme.md') ?? null)

const { data: readmeContent } = await useAsyncData(
  'repo-readme',
  async () => {
    if (!repo.value || !readmeFile.value) return null
    const res = await fetch(`${apiBase}/raw/${repo.value.owner.username}/${repo.value.slug}/${encodeURIComponent(readmeFile.value.original_name)}`)
    if (!res.ok) return null
    return await res.text()
  },
  { watch: [repo, readmeFile] },
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
  const blocks = escaped.split(/\n{2,}/).map((part) => part.trim()).filter(Boolean)
  return blocks.map((block) => {
    if (block.startsWith('### ')) return `<h3>${block.slice(4)}</h3>`
    if (block.startsWith('## ')) return `<h2>${block.slice(3)}</h2>`
    if (block.startsWith('# ')) return `<h1>${block.slice(2)}</h1>`
    if (block.startsWith('- ')) {
      const items = block.split('\n').map((line) => `<li>${line.replace(/^-\s+/, '')}</li>`).join('')
      return `<ul>${items}</ul>`
    }
    if (block.startsWith('```') && block.endsWith('```')) {
      return `<pre><code>${block.slice(3, -3).trim()}</code></pre>`
    }
    const withInline = block
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
      .replace(/\n/g, '<br>')
    return `<p>${withInline}</p>`
  }).join('')
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
