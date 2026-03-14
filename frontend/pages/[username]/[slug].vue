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
            <Icon name="mdilocal:repo-clone" class="w-4 h-4 text-muted" />
            <NuxtLink :to="`/${repo.owner.username}/repos`" class="text-muted hover:underline">{{ repo.owner.username }}</NuxtLink>
            <span class="text-muted">/</span>
            <span class="font-semibold">{{ repo.name }}</span>
            <VerificationBadge :status="displayStatus" />
            <span class="text-xs px-1.5 py-0.5 rounded border border-border font-mono text-muted">
              {{ repo.is_public ? 'Public' : 'Private' }}
            </span>
          </div>
          <p v-if="repo.description" class="text-sm text-muted">{{ repo.description }}</p>
          <MirrorSourceBox :repo="repo" class="mt-4 w-full" />
        </div>
        <div class="flex items-center gap-2 shrink-0" v-if="isOwner">
          <button v-if="repo.verification_status === 'unverified'" @click="requestVerify" class="btn-secondary text-sm py-1.5">
            <Icon name="mdilocal:shield-check-outline" class="w-4 h-4" /> Request Verification
          </button>
          <button @click="openRepoDetailsEdit" class="btn-secondary text-sm py-1.5">
            <Icon name="mdilocal:pencil-outline" class="w-4 h-4" /> Edit details
          </button>
          <NuxtLink :to="`/user/repos/${repo.owner.username}/${repo.slug}/upload`" class="btn-primary text-sm py-1.5">
            <Icon name="mdilocal:upload" class="w-4 h-4" /> Upload files
          </NuxtLink>
          <button @click="openDeleteRepoModal" class="btn-danger text-sm py-1.5">
            <Icon name="mdilocal:trash-can-outline" class="w-4 h-4" /> Delete repo
          </button>
        </div>
      </div>

      <div class="flex flex-wrap gap-5 text-xs text-muted font-mono mb-6 border-b border-border pb-4">
        <span class="flex items-center gap-1.5"><Icon name="mdilocal:file-multiple-outline" class="w-4 h-4" />{{ repo.file_count }} files</span>
        <span class="flex items-center gap-1.5"><Icon name="mdilocal:download-outline" class="w-4 h-4" />{{ repo.download_count.toLocaleString() }}</span>
        <span class="flex items-center gap-1.5"><Icon name="mdilocal:repo-clone" class="w-4 h-4" />{{ repo.clone_count.toLocaleString() }} clones</span>
        <span class="flex items-center gap-1.5"><Icon name="mdilocal:database-outline" class="w-4 h-4" />{{ formatBytes(repo.total_size) }}</span>
        <span class="ml-auto flex items-center gap-1.5"><Icon name="mdilocal:clock-outline" class="w-4 h-4" />{{ formatRelative(repo.updated_at) }}</span>
      </div>

      <div class="card overflow-hidden relative">
        <div class="px-4 py-3 border-b border-border flex items-center justify-between">
          <span class="text-sm font-semibold">Files</span>
          <span class="text-xs text-muted font-mono">{{ tree?.files?.length || 0 }} files · {{ tree?.directories?.length || 0 }} folders</span>
        </div>
        <div v-if="breadcrumbSegments.length" class="px-4 py-2 border-b border-border flex items-center gap-1.5 text-xs font-mono text-muted">
          <button class="hover:underline text-foreground disabled:opacity-60 disabled:cursor-not-allowed" :disabled="isDirectorySwitching" @click="navigateToPath('')">root</button>
          <span>/</span>
          <template v-for="(segment, index) in breadcrumbSegments" :key="`${segment}-${index}`">
            <button v-if="index < breadcrumbSegments.length - 1" class="hover:underline text-foreground disabled:opacity-60 disabled:cursor-not-allowed" :disabled="isDirectorySwitching" @click="navigateToPath(breadcrumbPaths[index])">{{ segment }}</button>
            <span v-else class="text-foreground">{{ segment }}</span>
            <span v-if="index < breadcrumbSegments.length - 1">/</span>
          </template>
        </div>
        <div
          v-if="isDirectorySwitching"
          class="pointer-events-none absolute inset-x-0 top-0 z-10 h-0.5 overflow-hidden"
        >
          <div class="h-full w-1/3 bg-blue-500 animate-pulse"></div>
        </div>
        <div v-if="!tree?.files?.length && !tree?.directories?.length" class="py-16 text-center text-muted">
          <Icon name="mdilocal:folder-directory" class="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p class="text-sm">No files or directories yet</p>
        </div>
        <div v-else class="divide-y divide-border">
          <div
            v-for="dir in tree?.directories || []"
            :key="`dir-${dir.path}`"
            class="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-surface-2/50 transition-colors"
          >
            <button
              class="flex-1 min-w-0 flex items-center gap-3 text-left"
              :disabled="isDirectorySwitching"
              @click="openDirectory(dir.path)"
            >
              <Icon name="mdilocal:folder-directory" class="w-4 h-4 text-muted shrink-0" />
              <span class="text-sm font-mono text-accent-2 truncate">{{ dir.name }}</span>
            </button>
            <span class="text-xs text-muted font-mono shrink-0">{{ formatBytes(dir.size_bytes) }}</span>
            <button
              v-if="isOwner"
              class="btn-ghost py-1 px-2 text-xs text-danger hover:text-danger"
              @click="onDeleteDirectory(dir.path)"
            >
              <Icon name="mdilocal:trash-can-outline" class="w-3.5 h-3.5" />
            </button>
          </div>
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

      <div class="hidden sm:block mt-3">
        <div class="flex w-full items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-xs text-muted font-mono shadow-sm">
          <Icon name="mdilocal:console" class="w-4 h-4 shrink-0 text-accent-2" />
          <span class="truncate">{{ cloneCurlCommand }}</span>
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


      <div v-if="showRepoEditModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4" @click.self="closeRepoDetailsEdit">
        <div class="card p-0 w-full max-w-lg overflow-hidden border border-border/80 shadow-2xl shadow-black/30">
          <div class="px-6 py-4 border-b border-border/80 bg-surface-2/40">
            <div class="flex items-center gap-2 text-sm font-medium">
              <Icon name="mdilocal:pencil-outline" class="w-4 h-4 text-accent-2" />
              Edit repository details
            </div>
            <p class="text-xs text-muted mt-1">Current values are prefilled. Update name and description, then save.</p>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="text-xs text-muted block mb-1.5">Repository name</label>
              <div class="relative">
                <Icon name="mdilocal:source-repository" class="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                <input v-model="repoEditForm.name" class="input pl-9" placeholder="my-cool-tool" />
              </div>
            </div>
            <div>
              <label class="text-xs text-muted block mb-1.5">Description (optional)</label>
              <div class="relative">
                <Icon name="mdilocal:file-document-outline" class="w-4 h-4 text-muted absolute left-3 top-3" />
                <textarea v-model="repoEditForm.description" class="input pl-9 min-h-[100px] resize-y" placeholder="What is this repo for?" />
              </div>
            </div>
            <div class="rounded-xl border border-border bg-surface-2/30 p-4 transition-all duration-300">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-medium">Mirror repository</p>
                  <p class="text-xs text-muted">Enable this if this repo mirrors another source platform.</p>
                </div>
                <button
                  type="button"
                  class="relative h-6 w-11 rounded-full overflow-hidden transition-colors duration-300"
                  :class="repoEditForm.is_mirror ? 'bg-accent-2' : 'bg-surface-3'"
                  @click="repoEditForm.is_mirror = !repoEditForm.is_mirror"
                >
                  <span class="absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all duration-300" :class="repoEditForm.is_mirror ? 'left-[1.375rem]' : 'left-0.5'" />
                </button>
              </div>
              <Transition name="fade-slide">
                <div v-if="repoEditForm.is_mirror" class="mt-4">
                  <label class="text-xs text-muted block mb-1.5">Main source URL</label>
                  <input v-model="repoEditForm.source_url" class="input" placeholder="https://github.com/publisher/repository" />
                </div>
              </Transition>
            </div>
            <p v-if="repoEditError" class="text-xs text-danger bg-danger/10 border border-danger/30 rounded px-3 py-2">{{ repoEditError }}</p>
            <div class="flex justify-end gap-2">
              <button class="btn-secondary text-sm py-1.5" @click="closeRepoDetailsEdit" :disabled="savingRepoDetails">Cancel</button>
              <button class="btn-primary text-sm py-1.5" @click="saveRepoDetailsEdit" :disabled="savingRepoDetails || !hasRepoDetailsChanges">
                <Icon v-if="savingRepoDetails" name="mdilocal:loading" class="w-4 h-4 animate-spin" />
                Save changes
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="showDeleteRepoModal" class="fixed inset-0 z-50 bg-black/55 flex items-center justify-center p-4" @click.self="closeDeleteRepoModal">
        <div class="card w-full max-w-md p-5">
          <div class="flex items-start gap-3 mb-3">
            <div class="w-9 h-9 rounded-full bg-danger/10 text-danger flex items-center justify-center shrink-0">
              <Icon name="mdilocal:alert" class="w-5 h-5" />
            </div>
            <div>
              <h3 class="text-base font-semibold">Delete repository?</h3>
              <p class="text-xs text-muted mt-1">This action is permanent. All files and folders will be removed.</p>
            </div>
          </div>
          <p class="text-xs text-muted mb-2">For safety, type <span class="font-mono text-foreground">{{ repo?.name }}</span> to confirm.</p>
          <input v-model="deleteRepoConfirmText" class="input text-sm" :placeholder="`Type ${repo?.name || 'repository name'}`" />
          <p v-if="deleteRepoError" class="text-xs text-danger mt-2">{{ deleteRepoError }}</p>
          <div class="flex justify-end gap-2 mt-4">
            <button class="btn-secondary text-sm py-1.5" @click="closeDeleteRepoModal" :disabled="deletingRepo">Cancel</button>
            <button class="btn-danger text-sm py-1.5" @click="deleteCurrentRepo" :disabled="deletingRepo || deleteRepoConfirmText !== repo?.name">
              {{ deletingRepo ? 'Deleting...' : 'Delete forever' }}
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
const router = useRouter()
const { get, post, put, delete: del } = useApi()
const apiBase = useRuntimeConfig().public.apiBase
const { user, isLoggedIn } = useAuth()
const loadingIndicator = useLoadingIndicator()

const isEditingFile = ref(false)
const editingFile = ref<RepoFile | null>(null)
const editContent = ref('')
const editError = ref('')
const savingEdit = ref(false)
const showDeleteRepoModal = ref(false)
const deleteRepoConfirmText = ref('')
const deletingRepo = ref(false)
const deleteRepoError = ref('')
const showRepoEditModal = ref(false)
const savingRepoDetails = ref(false)
const repoEditError = ref('')
const repoEditForm = reactive({ name: '', description: '', is_mirror: false, source_url: '' })
const repoOriginalDetails = reactive({ name: '', description: '', is_mirror: false, source_url: '' })

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

function normalizeRoutePath(value: unknown) {
  const raw = Array.isArray(value) ? value[0] : value
  if (typeof raw !== 'string') return ''
  return raw
    .replace(/\\/g, '/')
    .split('/')
    .map((part) => part.trim())
    .filter((part) => part && part !== '.' && part !== '..')
    .join('/')
}

const currentPath = ref(normalizeRoutePath(route.query.path))
const newDirectory = ref('')
const isNavigatingPath = ref(false)

interface RepoTreeDirectory {
  name: string
  path: string
  size_bytes: number
}

interface RepoTree {
  path: string
  directories: RepoTreeDirectory[]
  files: RepoFile[]
}

const { data: tree, pending: treePending, refresh: refreshTree } = await useAsyncData(
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

const cloneArchiveUrl = computed(() => {
  if (!repo.value) return ''
  return `${apiBase}/api/${encodeURIComponent(repo.value.owner.username)}/${encodeURIComponent(repo.value.slug)}/clone`
})

const cloneCurlCommand = computed(() => {
  if (!repo.value) return ''
  return `curl -L "${cloneArchiveUrl.value}" -o ${repo.value.slug}.zip`
})

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
    const response = await fetch(`${apiBase}/raw/${repo.value?.owner.username}/${repo.value?.slug}/${encodePathForUrl(fullPath)}`)
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

function resolveReadmeAssetUrl(url: string) {
  if (!url || !repo.value) return url
  if (url.startsWith('#') || url.startsWith('//') || url.startsWith('data:')) return url
  if (/^(https?:|mailto:|tel:)/i.test(url)) return url

  const normalized = url.startsWith('/') ? url.slice(1) : url.replace(/^\.\//, '')
  if (!normalized || normalized.startsWith('../')) return url

  const encodedPath = normalized.split('/').map((segment) => encodeURIComponent(segment)).join('/')
  return `${apiBase}/raw/${repo.value.owner.username}/${repo.value.slug}/${encodedPath}`
}

function markdownToHtml(content: string) {
  const lines = content.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let inCode = false
  let listType: 'ul' | 'ol' | null = null

  const closeList = () => {
    if (listType) {
      html.push(`</${listType}>`)
      listType = null
    }
  }

  const inline = (line: string) => escapeHtml(line)
    .replace(/\[!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]+)")?\)\]\(([^)\s]+)\)/g, (_m, alt, src, title, href) => {
      const titleAttr = title ? ` title="${title}"` : ''
      const resolvedHref = resolveReadmeAssetUrl(href)
      const externalAttrs = /^https?:\/\//i.test(resolvedHref) ? ' target="_blank" rel="noopener noreferrer"' : ''
      return `<a href="${resolvedHref}"${externalAttrs}><img src="${resolveReadmeAssetUrl(src)}" alt="${alt}"${titleAttr} loading="lazy" decoding="async"></a>`
    })
    .replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]+)")?\)/g, (_m, alt, src, title) => {
      const titleAttr = title ? ` title="${title}"` : ''
      return `<img src="${resolveReadmeAssetUrl(src)}" alt="${alt}"${titleAttr} loading="lazy" decoding="async">`
    })
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_m, text, href) => {
      const resolvedHref = resolveReadmeAssetUrl(href)
      const externalAttrs = /^https?:\/\//i.test(resolvedHref) ? ' target="_blank" rel="noopener noreferrer"' : ''
      return `<a href="${resolvedHref}"${externalAttrs}>${text}</a>`
    })
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')

  for (let index = 0; index < lines.length; index += 1) {
    const rawLine = lines[index]
    const line = rawLine.trimEnd()
    const trimmed = line.trim()

    if (line.startsWith('```')) {
      closeList()
      html.push(inCode ? '</code></pre>' : '<pre><code>')
      inCode = !inCode
      continue
    }

    if (inCode) {
      html.push(`${escapeHtml(rawLine)}\n`)
      continue
    }

    if (trimmed.startsWith('<')) {
      closeList()
      html.push(rawLine)
      continue
    }

    if (!trimmed) {
      closeList()
      continue
    }

    if (line.includes('|') && index + 1 < lines.length && /^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$/.test(lines[index + 1])) {
      closeList()
      const headerCells = line.split('|').map((cell) => cell.trim()).filter(Boolean)
      const alignRow = lines[index + 1].split('|').map((cell) => cell.trim()).filter(Boolean)
      html.push('<table><thead><tr>')
      headerCells.forEach((cell, cellIndex) => {
        const align = alignRow[cellIndex] || ''
        const style = align.startsWith(':') && align.endsWith(':') ? ' style="text-align:center"' : align.endsWith(':') ? ' style="text-align:right"' : ''
        html.push(`<th${style}>${inline(cell)}</th>`)
      })
      html.push('</tr></thead><tbody>')
      index += 2
      while (index < lines.length && lines[index].includes('|') && lines[index].trim()) {
        const rowCells = lines[index].split('|').map((cell) => cell.trim()).filter(Boolean)
        html.push('<tr>')
        rowCells.forEach((cell, cellIndex) => {
          const align = alignRow[cellIndex] || ''
          const style = align.startsWith(':') && align.endsWith(':') ? ' style="text-align:center"' : align.endsWith(':') ? ' style="text-align:right"' : ''
          html.push(`<td${style}>${inline(cell)}</td>`)
        })
        html.push('</tr>')
        index += 1
      }
      html.push('</tbody></table>')
      index -= 1
      continue
    }

    if (line.includes('|') && index + 1 < lines.length && /^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$/.test(lines[index + 1])) {
      closeList()
      const headerCells = line.split('|').map((cell) => cell.trim()).filter(Boolean)
      const alignRow = lines[index + 1].split('|').map((cell) => cell.trim()).filter(Boolean)
      html.push('<table><thead><tr>')
      headerCells.forEach((cell, cellIndex) => {
        const align = alignRow[cellIndex] || ''
        const style = align.startsWith(':') && align.endsWith(':') ? ' style="text-align:center"' : align.endsWith(':') ? ' style="text-align:right"' : ''
        html.push(`<th${style}>${inline(cell)}</th>`)
      })
      html.push('</tr></thead><tbody>')
      index += 2
      while (index < lines.length && lines[index].includes('|') && lines[index].trim()) {
        const rowCells = lines[index].split('|').map((cell) => cell.trim()).filter(Boolean)
        html.push('<tr>')
        rowCells.forEach((cell, cellIndex) => {
          const align = alignRow[cellIndex] || ''
          const style = align.startsWith(':') && align.endsWith(':') ? ' style="text-align:center"' : align.endsWith(':') ? ' style="text-align:right"' : ''
          html.push(`<td${style}>${inline(cell)}</td>`)
        })
        html.push('</tr>')
        index += 1
      }
      html.push('</tbody></table>')
      index -= 1
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

    const paragraphLines = [line]
    while (index + 1 < lines.length) {
      const nextLine = lines[index + 1].trimEnd()
      const nextTrimmed = nextLine.trim()
      if (!nextTrimmed) break
      if (nextLine.startsWith('```') || nextLine.startsWith('#') || nextLine.startsWith('> ') || /^[-*]\s+/.test(nextLine) || /^\d+\.\s+/.test(nextLine) || /^-{3,}$/.test(nextLine) || /^\*{3,}$/.test(nextLine) || nextTrimmed.startsWith('<')) break
      if (nextLine.includes('|') && index + 2 < lines.length && /^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$/.test(lines[index + 2])) break
      paragraphLines.push(nextLine)
      index += 1
    }

    html.push(`<p>${inline(paragraphLines.join(' '))}</p>`)
  }

  closeList()
  if (inCode) html.push('</code></pre>')
  return html.join('')
}

const readmeHtml = computed(() => (readmeContent.value ? markdownToHtml(readmeContent.value) : ''))

const breadcrumbSegments = computed(() => (currentPath.value ? currentPath.value.split('/') : []))
const breadcrumbPaths = computed(() => breadcrumbSegments.value.map((_, index) => breadcrumbSegments.value.slice(0, index + 1).join('/')))
const isDirectorySwitching = computed(() => treePending.value || isNavigatingPath.value)

function joinPath(base: string, next: string) {
  return [base, next].filter(Boolean).join('/')
}

function encodePathForUrl(path: string) {
  return path.split('/').map((segment) => encodeURIComponent(segment)).join('/')
}

async function navigateToPath(path: string) {
  const normalized = normalizeRoutePath(path)
  if (normalized === currentPath.value || isNavigatingPath.value) return

  isNavigatingPath.value = true
  loadingIndicator.start()
  try {
    currentPath.value = normalized
    await router.push({
      path: route.path,
      query: normalized ? { ...route.query, path: normalized } : Object.fromEntries(Object.entries(route.query).filter(([key]) => key !== 'path')),
    })
  } finally {
    isNavigatingPath.value = false
    loadingIndicator.finish()
  }
}

async function openDirectory(path: string) {
  if (treePending.value || isNavigatingPath.value) return
  await navigateToPath(path)
}

watch(
  () => route.query.path,
  (value) => {
    const normalized = normalizeRoutePath(value)
    if (normalized !== currentPath.value) {
      currentPath.value = normalized
    }
  },
)

async function createDirectory() {
  if (!repo.value || !newDirectory.value.trim()) return
  const target = joinPath(currentPath.value, newDirectory.value.trim())
  await post(`/api/users/${repo.value.owner.username}/repos/${repo.value.slug}/directories`, { path: target })
  newDirectory.value = ''
  await refreshTree()
}


const hasRepoDetailsChanges = computed(() => (
  repoEditForm.name !== repoOriginalDetails.name
  || repoEditForm.description !== repoOriginalDetails.description
  || repoEditForm.is_mirror !== repoOriginalDetails.is_mirror
  || repoEditForm.source_url !== repoOriginalDetails.source_url
))

function openRepoDetailsEdit() {
  if (!repo.value) return
  repoEditForm.name = repo.value.name
  repoEditForm.description = repo.value.description || ''
  repoOriginalDetails.name = repo.value.name
  repoEditForm.is_mirror = repo.value.is_mirror
  repoEditForm.source_url = repo.value.source_url || ''
  repoOriginalDetails.description = repo.value.description || ''
  repoOriginalDetails.is_mirror = repo.value.is_mirror
  repoOriginalDetails.source_url = repo.value.source_url || ''
  repoEditError.value = ''
  showRepoEditModal.value = true
}

function closeRepoDetailsEdit() {
  if (savingRepoDetails.value) return
  showRepoEditModal.value = false
  repoEditError.value = ''
}

async function saveRepoDetailsEdit() {
  if (!repo.value || !hasRepoDetailsChanges.value) return
  savingRepoDetails.value = true
  repoEditError.value = ''
  try {
    const updated = await put<Repo>(`/api/repos/${repo.value.id}`, {
      name: repoEditForm.name,
      description: repoEditForm.description || null,
      is_mirror: repoEditForm.is_mirror,
      source_url: repoEditForm.is_mirror ? (repoEditForm.source_url || null) : null,
    })
    showRepoEditModal.value = false
    repo.value = updated
    const expectedPath = `/${updated.owner.username}/${updated.slug}`
    if (route.path !== expectedPath) {
      await navigateTo(expectedPath)
      return
    }
    await Promise.all([refreshRepo(), refreshTree()])
  } catch (error: any) {
    repoEditError.value = error?.message || 'Failed to update repository details.'
  } finally {
    savingRepoDetails.value = false
  }
}

function openDeleteRepoModal() {
  deleteRepoError.value = ''
  deleteRepoConfirmText.value = ''
  showDeleteRepoModal.value = true
}

function closeDeleteRepoModal() {
  if (deletingRepo.value) return
  showDeleteRepoModal.value = false
  deleteRepoError.value = ''
  deleteRepoConfirmText.value = ''
}

async function deleteCurrentRepo() {
  if (!repo.value) return
  if (deleteRepoConfirmText.value !== repo.value.name) {
    deleteRepoError.value = 'Repository name does not match.'
    return
  }

  deletingRepo.value = true
  deleteRepoError.value = ''
  try {
    await del(`/api/repos/${repo.value.id}`)
    showDeleteRepoModal.value = false
    await navigateTo(`/${repo.value.owner.username}/repos`)
  } catch (error: any) {
    deleteRepoError.value = error?.message || 'Failed to delete repository.'
  } finally {
    deletingRepo.value = false
  }
}

async function requestVerify() {
  try {
    await post(`/api/repos/${repo.value?.id}/request-verification`, {})
  } catch {}
  await refreshRepo()
}

async function onDeleteFile(id: number) {
  if (!confirm('Are you sure you want to remove this file?')) return
  await del(`/api/files/${id}`)
  await Promise.all([refreshTree(), refreshRepo()])
}

async function onDeleteDirectory(path: string) {
  if (!repo.value) return
  if (!confirm(`Are you sure you want to remove this folder and all files inside it?\n\n${path}`)) return
  const query = `?path=${encodeURIComponent(path)}`
  await del(`/api/users/${repo.value.owner.username}/repos/${repo.value.slug}/directories${query}`)
  await Promise.all([refreshTree(), refreshRepo()])
}

useSeoMeta({ title: computed(() => `${route.params.username}/${route.params.slug}`) })
</script>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.28s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
