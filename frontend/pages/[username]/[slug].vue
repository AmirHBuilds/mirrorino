<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <div v-if="pending" class="animate-pulse space-y-4">
      <div class="h-8 bg-surface-2 rounded w-64"></div>
      <div class="h-4 bg-surface-2 rounded w-96"></div>
      <div class="card h-48"></div>
    </div>
    <template v-else-if="repo">
      <!-- Unverified warning -->
      <div v-if="repo.verification_status === 'unverified'" class="flex items-start gap-3 bg-warning/5 border border-warning/30 rounded-lg px-4 py-3 mb-6 text-sm text-warning">
        <Icon name="mdi:alert" class="w-5 h-5 shrink-0 mt-0.5" />
        <span><strong>Unverified repository.</strong> Not reviewed by admins. Download at your own risk.</span>
      </div>

      <!-- Header -->
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
          <NuxtLink :to="`/user/repos/${repo.id}/upload`" class="btn-primary text-sm py-1.5">
            <Icon name="mdi:upload" class="w-4 h-4" /> Upload files
          </NuxtLink>
        </div>
      </div>

      <!-- Stats -->
      <div class="flex flex-wrap gap-5 text-xs text-muted font-mono mb-6 border-b border-border pb-4">
        <span class="flex items-center gap-1.5"><Icon name="mdi:file-multiple-outline" class="w-4 h-4" />{{ repo.file_count }} files</span>
        <span class="flex items-center gap-1.5"><Icon name="mdi:download-outline" class="w-4 h-4" />{{ repo.download_count.toLocaleString() }}</span>
        <span class="flex items-center gap-1.5"><Icon name="mdi:database-outline" class="w-4 h-4" />{{ formatBytes(repo.total_size) }}</span>
        <span class="ml-auto flex items-center gap-1.5"><Icon name="mdi:clock-outline" class="w-4 h-4" />{{ formatRelative(repo.updated_at) }}</span>
      </div>

      <!-- Raw install helper -->
      <div class="card p-4 mb-6">
        <p class="text-xs text-muted font-mono uppercase tracking-wider mb-2">Raw install command</p>
        <div class="font-mono text-xs bg-surface-2 rounded p-3 flex items-center gap-2 overflow-x-auto">
          <span class="flex-1">bash &lt;(curl -Ls https://api.downloadino.com/raw/{{ repo.owner.username }}/{{ repo.slug }}/install.sh)</span>
          <button @click="copy" class="shrink-0 text-muted hover:text-fg transition-colors ml-2">
            <Icon :name="copied ? 'mdi:check' : 'mdi:content-copy'" class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Files list -->
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
          <FileRow v-for="file in files" :key="file.id" :file="file" :can-delete="isOwner" @delete="onDeleteFile" />
        </div>
      </div>
    </template>
    <div v-else class="text-center py-24 text-muted">Repository not found</div>
  </div>
</template>

<script setup lang="ts">
import { formatBytes, formatRelative } from '~/utils/format'
import type { Repo, RepoFile } from '~/types'

const route  = useRoute()
const { get, post, delete: del } = useApi()
const { user, isLoggedIn } = useAuth()
const copied = ref(false)

const { data: repo, pending, refresh: refreshRepo } = await useAsyncData('repo-detail', async () => {
  const list = await get<Repo[]>(`/api/repos/?q=${route.params.slug}&limit=50`)
  return list.find(r => r.slug === route.params.slug && r.owner.username === route.params.username) ?? null
})

const { data: files, refresh: refreshFiles } = await useAsyncData('repo-files', async () => {
  if (!repo.value) return []
  return get<RepoFile[]>(`/api/repos/${repo.value.id}/files`)
})

const isOwner = computed(() => isLoggedIn.value && user.value?.username === route.params.username)

async function copy() {
  await navigator.clipboard.writeText(`bash <(curl -Ls https://api.downloadino.com/raw/${repo.value?.owner.username}/${repo.value?.slug}/install.sh)`)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

async function requestVerify() {
  try { await post(`/api/repos/${repo.value?.id}/request-verification`, {}) } catch {}
  await refreshRepo()
}

async function onDeleteFile(id: number) {
  await del(`/api/files/${id}`)
  await refreshFiles()
}

useSeoMeta({ title: computed(() => `${route.params.username}/${route.params.slug}`) })
</script>
