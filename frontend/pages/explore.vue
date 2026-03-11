<template>
  <div class="max-w-7xl mx-auto px-4 py-8">
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
      <h1 class="text-2xl font-bold">Explore repositories</h1>
      <div class="w-full sm:w-auto flex flex-col sm:flex-row gap-2 sm:items-center">
        <select v-model="sort" class="input py-1.5 text-sm sm:w-48" @change="refresh">
          <option value="downloads">Most downloaded</option>
          <option value="clones">Most cloned</option>
          <option value="recent">Recently updated</option>
        </select>
      </div>
    </div>

    <div v-if="pending" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 9" :key="i" class="card p-4 animate-pulse h-32"></div>
    </div>
    <div v-else-if="repos?.length === 0" class="text-center py-20 text-muted">
      <Icon name="mdilocal:source-repository-multiple" class="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p>No repositories found</p>
    </div>
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <RepoCard v-for="repo in repos" :key="repo.id" :repo="repo" />
    </div>

    <AdSlot position="explore_inline" :limit="3" compact wrapper-class="mt-8" />
  </div>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'
useSeoMeta({ title: 'Explore' })
const route = useRoute()
const router = useRouter()
const allowedSorts = new Set(['downloads', 'clones', 'recent'])
const querySort = (route.query.sort as string) || 'downloads'
const sort = ref(allowedSorts.has(querySort) ? querySort : 'downloads')
const { get } = useApi()
const { data: repos, pending, refresh } = await useAsyncData(
  () => `explore:${sort.value}`,
  () => get<Repo[]>(`/api/repos/?limit=30&sort=${sort.value}`),
  { server: false, default: () => [] },
)
watch(sort, () => {
  const query: Record<string, string> = { ...route.query } as Record<string, string>
  if (sort.value === 'downloads') delete query.sort
  else query.sort = sort.value
  router.replace({ query })
})
</script>
