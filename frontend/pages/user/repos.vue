<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold">My Repositories</h1>
      <button @click="showCreate = true" class="btn-primary py-1.5 text-sm">
        <Icon name="mdi:plus" class="w-4 h-4" /> New repository
      </button>
    </div>

    <!-- Storage bar -->
    <div class="card p-4 mb-6" v-if="user">
      <p class="text-xs font-mono text-muted uppercase tracking-wider mb-3">Storage usage</p>
      <StorageBar :used="user.storage_used" :limit="user.storage_limit" />
      <p v-if="user.storage_usage_percent > 80" class="text-xs text-warning mt-3 flex items-center gap-1.5">
        <Icon name="mdi:alert-outline" class="w-4 h-4" />
        Running low. Delete repos or request verification for more space.
      </p>
    </div>

    <div v-if="pending" class="space-y-3">
      <div v-for="i in 3" :key="i" class="card p-4 h-24 animate-pulse"></div>
    </div>
    <div v-else-if="!repos?.length" class="card py-16 text-center text-muted">
      <Icon name="mdi:source-repository-multiple" class="w-10 h-10 mx-auto mb-3 opacity-30" />
      <p class="text-sm">No repositories yet.</p>
      <button @click="showCreate = true" class="btn-secondary mt-4 text-sm">Create your first repo</button>
    </div>
    <div v-else class="space-y-3">
      <div v-for="repo in repos" :key="repo.id" class="card p-4 hover:border-surface-3 transition-colors">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <NuxtLink :to="`/${repo.owner.username}/${repo.slug}`" class="font-medium text-accent-2 hover:underline text-sm">{{ repo.name }}</NuxtLink>
              <VerificationBadge :status="repo.verification_status" />
              <span class="text-xs font-mono text-muted border border-border px-1.5 py-0.5 rounded">{{ repo.is_public ? 'Public' : 'Private' }}</span>
            </div>
            <p v-if="repo.description" class="text-xs text-muted truncate">{{ repo.description }}</p>
            <div class="flex items-center gap-4 mt-2 text-xs text-muted font-mono">
              <span>{{ repo.file_count }} files</span>
              <span>{{ formatBytes(repo.total_size) }}</span>
              <span>{{ formatRelative(repo.updated_at) }}</span>
            </div>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <NuxtLink :to="`/user/repos/${repo.id}/upload`" class="btn-ghost py-1 px-2 text-xs">Upload</NuxtLink>
            <button @click="deleteRepo(repo.id)" class="btn-ghost py-1 px-2 text-xs text-danger hover:text-danger">
              <Icon name="mdi:trash-can-outline" class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create repo modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4" @click.self="showCreate=false">
      <div class="card p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-4">New repository</h2>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-muted block mb-1.5">Repository name</label>
            <input v-model="newRepo.name" class="input" placeholder="my-cool-tool" />
          </div>
          <div>
            <label class="text-xs text-muted block mb-1.5">Description (optional)</label>
            <input v-model="newRepo.description" class="input" placeholder="What is this repo for?" />
          </div>
          <label class="flex items-center gap-2 text-sm cursor-pointer">
            <input v-model="newRepo.is_public" type="checkbox" class="rounded" />
            Public repository
          </label>
          <p v-if="createError" class="text-xs text-danger">{{ createError }}</p>
          <div class="flex gap-2 pt-2">
            <button @click="showCreate=false" class="btn-secondary flex-1 justify-center">Cancel</button>
            <button @click="createRepo" class="btn-primary flex-1 justify-center" :disabled="creating">
              <Icon v-if="creating" name="mdi:loading" class="w-4 h-4 animate-spin" />
              Create
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatBytes, formatRelative } from '~/utils/format'
import type { Repo } from '~/types'
definePageMeta({ middleware: 'auth' })
useSeoMeta({ title: 'My Repositories' })

const { get, post, delete: del } = useApi()
const { user } = useAuth()

const { data: repos, pending, refresh } = await useAsyncData('my-repos', () => get<Repo[]>('/api/repos/mine'))

const showCreate  = ref(false)
const creating    = ref(false)
const createError = ref('')
const newRepo     = reactive({ name: '', description: '', is_public: true })

async function createRepo() {
  creating.value = true
  createError.value = ''
  try {
    await post('/api/repos/', { ...newRepo })
    showCreate.value = false
    Object.assign(newRepo, { name: '', description: '', is_public: true })
    await refresh()
  } catch (e: any) {
    createError.value = e.message
  } finally {
    creating.value = false
  }
}


async function deleteRepo(id: number) {
  if (!confirm('Delete this repository and all its files?')) return
  await del(`/api/repos/${id}`)
  await refresh()
}
</script>
