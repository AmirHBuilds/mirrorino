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
          <span class="text-xs text-muted font-mono">{{ tree?.files?.length || 0 }} files · {{ tree?.directories?.length || 0 }} folders</span>
        </div>
        <div class="px-4 py-2 border-b border-border flex items-center gap-1.5 text-xs font-mono text-muted">
          <span>/</span>
          <template v-for="(segment, index) in breadcrumbSegments" :key="`${segment}-${index}`">
            <button class="hover:underline text-foreground" @click="navigateToPath(breadcrumbPaths[index])">{{ segment }}</button>
            <span v-if="index < breadcrumbSegments.length - 1">/</span>
          </template>
        </div>
        <div v-if="!tree?.files?.length && !tree?.directories?.length" class="py-16 text-center text-muted">
          <Icon name="mdilocal:folder-directory" class="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p class="text-sm">No files or directories yet</p>
        </div>
        <div v-else class="divide-y divide-border">
          <button
            v-for="dir in tree?.directories || []"
            :key="`dir-${dir}`"
            class="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-surface-2/50 transition-colors text-left"
            @click="navigateToPath(joinPath(currentPath, dir))"
          >
            <Icon name="mdilocal:folder-directory" class="w-4 h-4 text-muted shrink-0" />
            <span class="text-sm font-mono text-accent-2">{{ dir }}</span>
          </button>
          <FileRow
            v-for="file in tree?.files || []"
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

      <div v-if="isOwner" class="mt-4 card p-4 space-y-3">
        <div class="rounded-md border border-border bg-surface-2/50 px-3 py-2 text-xs text-muted">
          Uploading and folder creation happen inside: <span class="font-mono text-foreground">/{{ currentPath || '' }}</span>
        </div>
        <div class="flex flex-col sm:flex-row gap-2 sm:items-center">
          <input v-model="newDirectory" class="input flex-1" placeholder="Create folder in current path (e.g. docs)" />
          <button class="btn-secondary text-sm py-1.5" @click="createDirectory">Create folder</button>
        </div>
        <UploadZone :repo-username="repo.owner.username" :repo-slug="repo.slug" :directory-path="currentPath" @uploaded="refreshTree" />
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

const currentPath = ref('')
const newDirectory = ref('')

interface RepoTree {
  path: string
  directories: string[]
  files: RepoFile[]
}

const { data: tree, refresh: refreshTree } = await useAsyncData(
  () => `repo-tree:${repo.value?.owner.username || route.params.username}:${repo.value?.slug || route.params.slug}:${currentPath.value}`,
  async () => {
    if (!repo.value) return { path: '', directories: [], files: [] }
    const query = currentPath.value ? `?path=${encodeURIComponent(currentPath.value)}` : ''
    return get<RepoTree>(`/api/users/${repo.value.owner.username}/repos/${repo.value.slug}/tree${query}`)
  },
  { watch: [repo, currentPath], server: false, default: () => ({ path: '', directories: [], files: [] }) },
)

const isOwner = computed(() => isLoggedIn.value && !!repo.value && user.value?.id === repo.value.owner.id)
const displayStatus = computed(() => repo.value ? visibleVerificationStatus(repo.value.verification_status, !!isOwner.value) : 'unverified')

const readmeFile = computed(() => tree.value?.files?.find((file) => file.original_name.toLowerCase() === 'readme.md' && !file.directory_path) ?? null)

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
    const fullPath = file.directory_path ? `${file.directory_path}/${file.original_name}` : file.original_name
    const response = await fetch(`${apiBase}/raw/${repo.value?.owner.username}/${repo.value?.slug}/${encodeURIComponent(fullPath)}`)
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
    await Promise.all([refreshTree(), refreshRepo()])
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

const breadcrumbSegments = computed(() => (currentPath.value ? currentPath.value.split('/') : []))
const breadcrumbPaths = computed(() => breadcrumbSegments.value.map((_, index) => breadcrumbSegments.value.slice(0, index + 1).join('/')))

function joinPath(base: string, next: string) {
  return [base, next].filter(Boolean).join('/')
}

function navigateToPath(path: string) {
  currentPath.value = path
}

async function createDirectory() {
  if (!repo.value || !newDirectory.value.trim()) return
  const target = joinPath(currentPath.value, newDirectory.value.trim())
  await post(`/api/users/${repo.value.owner.username}/repos/${repo.value.slug}/directories`, { path: target })
  newDirectory.value = ''
  await refreshTree()
}

async function requestVerify() {
  try {
    await post(`/api/repos/${repo.value?.id}/request-verification`, {})
  } catch {}
  await refreshRepo()
}

async function onDeleteFile(id: number) {
  await del(`/api/files/${id}`)
  await refreshTree()
}

useSeoMeta({ title: computed(() => `${route.params.username}/${route.params.slug}`) })
</script>
