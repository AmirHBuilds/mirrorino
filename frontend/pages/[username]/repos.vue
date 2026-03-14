<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold">{{ isOwner ? 'My Repositories' : `${username}'s Repositories` }}</h1>
      <button v-if="isOwner" @click="showCreate = true" class="btn-primary py-1.5 text-sm">
        <Icon name="mdilocal:plus" class="w-4 h-4" /> New repository
      </button>
    </div>

    <div class="card p-4 mb-6" v-if="isOwner && user">
      <p class="text-xs font-mono text-muted uppercase tracking-wider mb-3">Storage usage</p>
      <StorageBar :used="user.storage_used" :limit="user.storage_limit" />
    </div>

    <div v-if="pending" class="space-y-3">
      <div v-for="i in 3" :key="i" class="card p-4 h-24 animate-pulse"></div>
    </div>
    <div v-else-if="!repos?.length" class="card py-16 text-center text-muted">
      <Icon name="mdilocal:source-repository-multiple" class="w-10 h-10 mx-auto mb-3 opacity-30" />
      <p class="text-sm">No repositories yet.</p>
      <button v-if="isOwner" @click="showCreate = true" class="btn-secondary mt-4 text-sm">Create your first repo</button>
    </div>
    <div v-else class="space-y-3">
      <div v-for="repo in repos" :key="repo.id" class="card p-4 hover:border-surface-3 transition-colors">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <NuxtLink :to="`/${repo.owner.username}/${repo.slug}`" class="font-medium text-accent-2 hover:underline text-sm">{{ repo.name }}</NuxtLink>
              <VerificationBadge :status="displayStatus(repo.verification_status)" />
              <span class="text-xs font-mono text-muted border border-border px-1.5 py-0.5 rounded">{{ repo.is_public ? 'Public' : 'Private' }}</span>
            </div>
            <p v-if="repo.description" class="text-xs text-muted truncate">{{ repo.description }}</p>
            <MirrorSourceBox :repo="repo" compact class="mt-2 w-full md:max-w-[32rem]" />
            <div class="flex items-center gap-4 mt-3 text-xs text-muted font-mono">
              <span>{{ repo.file_count }} files</span>
              <span>{{ formatBytes(repo.total_size) }}</span>
              <span>{{ formatRelative(repo.updated_at) }}</span>
            </div>
          </div>
          <div v-if="isOwner" class="flex items-center gap-1 shrink-0">
            <button @click.stop="goToUpload(repo)" class="btn-ghost py-1 px-2 text-xs">Upload</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCreate" class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 px-4" @click.self="showCreate=false">
      <div class="card p-6 w-full max-w-2xl border border-border/80 shadow-2xl shadow-black/30">
        <h2 class="text-lg font-semibold mb-4">New repository</h2>
        <div class="space-y-4">
          <div>
            <label class="text-xs text-muted block mb-1.5">Repository name</label>
            <input v-model="newRepo.name" class="input" placeholder="my-cool-tool" />
          </div>
          <div>
            <label class="text-xs text-muted block mb-1.5">Description (optional)</label>
            <input v-model="newRepo.description" class="input" placeholder="What is this repo for?" />
          </div>

          <div class="rounded-xl border border-border bg-surface-2/30 p-4 transition-all duration-300">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-sm font-medium">Is this a mirror?</p>
                <p class="text-xs text-muted">Let users know this repo mirrors another source repository.</p>
              </div>
              <button
                type="button"
                class="relative h-6 w-11 rounded-full overflow-hidden transition-colors duration-300"
                :class="newRepo.is_mirror ? 'bg-accent-2' : 'bg-surface-3'"
                @click="toggleMirror"
              >
                <span
                  class="absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all duration-300"
                  :class="newRepo.is_mirror ? 'left-[1.375rem]' : 'left-0.5'"
                />
              </button>
            </div>
            <Transition name="fade-slide">
              <div v-if="newRepo.is_mirror" class="mt-4">
                <label class="text-xs text-muted block mb-1.5">Main source URL</label>
                <input v-model="newRepo.source_url" class="input" placeholder="https://github.com/publisher/repo" />
                <MirrorSourceBox :repo="mirrorPreviewRepo" compact class="mt-2" />
              </div>
            </Transition>
          </div>

          <div class="text-xs text-muted bg-surface-2/70 border border-border rounded px-3 py-2">
            Private repositories are disabled for self-service accounts.
            <NuxtLink to="/contact" class="text-accent-2 hover:underline">Contact support</NuxtLink>
            if you need private repositories.
          </div>
          <p v-if="createError" class="text-xs text-danger">{{ createError }}</p>
          <div class="flex gap-2 pt-2">
            <button @click="showCreate=false" class="btn-secondary flex-1 justify-center">Cancel</button>
            <button @click="createRepo" class="btn-primary flex-1 justify-center" :disabled="creating">
              <Icon v-if="creating" name="mdilocal:loading" class="w-4 h-4 animate-spin" />Create
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
import { visibleVerificationStatus, type VerificationStatus } from '~/utils/repo'

const route = useRoute()
const { get, post } = useApi()
const { user, fetchUser } = useAuth()
const username = computed(() => String(route.params.username || ''))

if (useCookie<string | null>('token').value && !user.value) await fetchUser()

const isOwner = computed(() => !!user.value && user.value.username === username.value)
const displayStatus = (status: VerificationStatus) => visibleVerificationStatus(status, !!isOwner.value)

const { data: repos, pending, refresh } = await useAsyncData(
  () => `user-repos:${username.value}:${isOwner.value ? 'mine' : 'public'}`,
  async () => {
    if (isOwner.value) return get<Repo[]>('/api/repos/mine')
    return get<Repo[]>(`/api/repos/users/${username.value}`)
  },
  { watch: [isOwner, username], server: false, default: () => [] },
)

const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const newRepo = reactive({ name: '', description: '', is_public: true, is_mirror: false, source_url: '' })

const mirrorPreviewRepo = computed<Repo>(() => ({
  id: 0,
  name: newRepo.name || 'mirror-preview',
  slug: 'mirror-preview',
  description: newRepo.description || null,
  is_public: true,
  verification_status: 'unverified',
  download_count: 0,
  clone_count: 0,
  is_mirror: newRepo.is_mirror,
  source_url: newRepo.source_url || null,
  owner: { id: 0, username: user.value?.username || 'you', role: 'user', created_at: '' },
  file_count: 0,
  total_size: 0,
  created_at: '',
  updated_at: '',
}))

function toggleMirror() {
  newRepo.is_mirror = !newRepo.is_mirror
  if (!newRepo.is_mirror) newRepo.source_url = ''
}

async function createRepo() {
  creating.value = true
  createError.value = ''
  try {
    await post('/api/repos/', {
      ...newRepo,
      source_url: newRepo.is_mirror ? newRepo.source_url : null,
    })
    showCreate.value = false
    Object.assign(newRepo, { name: '', description: '', is_public: true, is_mirror: false, source_url: '' })
    await refresh()
  } catch (e: any) {
    createError.value = e.message
  } finally {
    creating.value = false
  }
}

function goToUpload(repo: Repo) {
  navigateTo(`/user/repos/${repo.owner.username}/${repo.slug}/upload`)
}

useSeoMeta({ title: computed(() => `${username.value} repos`) })
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
