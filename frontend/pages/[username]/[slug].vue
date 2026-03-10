<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <div v-if="pending" class="animate-pulse space-y-4">
      <div class="h-8 bg-surface-2 rounded w-64"></div>
      <div class="h-4 bg-surface-2 rounded w-96"></div>
      <div class="card h-48"></div>
    </div>
    <template v-else-if="repo">
      <div v-if="displayStatus === 'rejected'" class="flex items-start gap-3 bg-danger/5 border border-danger/30 rounded-lg px-4 py-3 mb-6 text-sm text-danger">
        <Icon name="mdilocal:alert-circle" class="w-5 h-5 shrink-0 mt-0.5" />
        <span><strong>Marked as spam.</strong> This repository was rejected during verification.</span>
      </div>
      <div v-else-if="displayStatus === 'unverified'" class="flex items-start gap-3 bg-warning/5 border border-warning/30 rounded-lg px-4 py-3 mb-6 text-sm text-warning">
        <Icon name="mdilocal:alert" class="w-5 h-5 shrink-0 mt-0.5" />
        <span><strong>Unverified repository.</strong> Not reviewed by admins. Download at your own risk.</span>
      </div>

      <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-6">
        <div>
          <div class="flex flex-wrap items-center gap-2 text-sm mb-2">
            <Icon name="mdilocal:source-repository" class="w-4 h-4 text-muted" />
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
            <Icon name="mdilocal:shield-check-outline" class="w-4 h-4" /> Request Verification
          </button>
          <NuxtLink :to="`/user/repos/${repo.owner.username}/${repo.slug}/upload`" class="btn-primary text-sm py-1.5">
            <Icon name="mdilocal:upload" class="w-4 h-4" /> Upload files
          </NuxtLink>
        </div>
      </div>

      <div class="flex flex-wrap gap-5 text-xs text-muted font-mono mb-6 border-b border-border pb-4">
        <span class="flex items-center gap-1.5"><Icon name="mdilocal:file-multiple-outline" class="w-4 h-4" />{{ repo.file_count }} files</span>
        <span class="flex items-center gap-1.5"><Icon name="mdilocal:download-outline" class="w-4 h-4" />{{ repo.download_count.toLocaleString() }}</span>
        <span class="flex items-center gap-1.5"><Icon name="mdilocal:database-outline" class="w-4 h-4" />{{ formatBytes(repo.total_size) }}</span>
        <span class="ml-auto flex items-center gap-1.5"><Icon name="mdilocal:clock-outline" class="w-4 h-4" />{{ formatRelative(repo.updated_at) }}</span>
      </div>

      <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b border-border flex items-center justify-between">
          <span class="text-sm font-semibold">Files</span>
          <span class="text-xs text-muted font-mono">{{ files?.length || 0 }} files</span>
        </div>
        <div v-if="!files?.length" class="py-16 text-center text-muted">
          <Icon name="mdilocal:folder-open-outline" class="w-10 h-10 mx-auto mb-3 opacity-30" />
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
            :can-edit="isOwner"
            @delete="onDeleteFile"
            @edit="startEditFile"
          />
        </div>
      </div>

      <div v-if="isEditingFile" class="fixed inset-0 z-50 bg-black/55 flex items-center justify-center p-4" @click.self="cancelEdit">
        <div class="card w-full max-w-4xl p-4">
          <div class="flex items-center justify-between gap-3 mb-3">
            <div>
              <h3 class="text-sm font-semibold">Edit file</h3>
              <p class="text-xs text-muted font-mono">{{ editingFile?.original_name }}</p>
            </div>
            <button class="btn-ghost py-1 px-2 text-xs" @click="cancelEdit">Close</button>
          </div>
          <p v-if="editError" class="text-xs text-danger mb-2">{{ editError }}</p>
          <textarea
            v-model="editContent"
            class="w-full min-h-[360px] rounded-md border border-border bg-surface px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-accent"
            placeholder="File content"
          />
          <div class="flex justify-end gap-2 mt-3">
            <button class="btn-secondary text-sm py-1.5" @click="cancelEdit" :disabled="savingEdit">Cancel</button>
            <button class="btn-primary text-sm py-1.5" @click="saveEditedFile" :disabled="savingEdit">
              {{ savingEdit ? 'Saving...' : 'Save changes' }}
            </button>
          </div>
        </div>
      </div>

      <AdSlot position="repo_inline" :limit="2" compact wrapper-class="mt-6" />

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
const { get, post, put, delete: del } = useApi()
const apiBase = useRuntimeConfig().public.apiBase
const { user, isLoggedIn } = useAuth()

const isEditingFile = ref(false)
const editingFile = ref<RepoFile | null>(null)
const editContent = ref('')
const editError = ref('')
const savingEdit = ref(false)

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

async function startEditFile(file: RepoFile) {
  editError.value = ''
  editingFile.value = file
  isEditingFile.value = true
  try {
    const response = await fetch(`${apiBase}/raw/${repo.value?.owner.username}/${repo.value?.slug}/${encodeURIComponent(file.original_name)}`)
    if (!response.ok) throw new Error('Failed to fetch current file content')
    editContent.value = await response.text()
  } catch {
    editContent.value = ''
    editError.value = 'Could not load current file content.'
  }
}

function cancelEdit() {
  isEditingFile.value = false
  editingFile.value = null
  editContent.value = ''
  editError.value = ''
}

async function saveEditedFile() {
  if (!editingFile.value) return
  savingEdit.value = true
  editError.value = ''
  try {
    await put(`/api/files/${editingFile.value.id}/content`, { content: editContent.value })
    await Promise.all([refreshFiles(), refreshRepo()])
    cancelEdit()
  } catch (error: any) {
    editError.value = error?.message || 'Failed to save file.'
  } finally {
    savingEdit.value = false
  }
}

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
