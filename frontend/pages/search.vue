<template>
  <div class="max-w-7xl mx-auto px-4 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold">Search repositories</h1>
      <p class="text-sm text-muted mt-1">Find repositories by name, slug, description, or owner username.</p>
    </div>

    <div class="card p-4 mb-6">
      <div class="relative">
        <Icon name="mdi:magnify" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted w-4 h-4" />
        <input
          v-model="q"
          @keyup.enter="runSearch"
          placeholder="Search repositories..."
          class="input pl-9 py-2 text-sm"
        />
      </div>
      <div class="flex items-center justify-between mt-3 text-xs text-muted font-mono">
        <span v-if="q.trim()">Query: {{ q.trim() }}</span>
        <span v-if="!pending && searched">{{ repos.length }} result(s)</span>
      </div>
    </div>

    <div v-if="pending" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 9" :key="i" class="card p-4 animate-pulse h-32"></div>
    </div>

    <div v-else-if="searched && repos.length === 0" class="card py-16 text-center text-muted">
      <Icon name="mdi:file-search-outline" class="w-10 h-10 mx-auto mb-3 opacity-40" />
      <p class="text-sm">No results found.</p>
      <p class="text-xs mt-1">Try another keyword, repository slug, or username.</p>
    </div>

    <div v-else-if="repos.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <RepoCard v-for="repo in repos" :key="repo.id" :repo="repo" />
    </div>

    <div v-else class="card py-16 text-center text-muted">
      <Icon name="mdi:magnify" class="w-10 h-10 mx-auto mb-3 opacity-40" />
      <p class="text-sm">Start searching to see repositories.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'

const route = useRoute()
const router = useRouter()
const { get } = useApi()
const q = ref(String(route.query.q || ''))
const searched = computed(() => q.value.trim().length > 0)

const { data: repos, pending, refresh } = await useAsyncData(
  () => `search:${q.value.trim()}`,
  async () => {
    if (!q.value.trim()) return []
    return get<Repo[]>(`/api/repos/?limit=60&q=${encodeURIComponent(q.value.trim())}`)
  },
  { server: false, default: () => [] },
)

async function runSearch() {
  const value = q.value.trim()
  await router.replace({ path: '/search', query: value ? { q: value } : {} })
  await refresh()
}

watch(
  () => route.query.q,
  (newQuery) => {
    q.value = String(newQuery || '')
    refresh()
  },
)

useSeoMeta({ title: 'Search' })
</script>
