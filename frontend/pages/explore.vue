<template>
  <div class="max-w-7xl mx-auto px-4 py-8">
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
      <h1 class="text-2xl font-bold">Explore repositories</h1>
      <div class="relative w-full sm:w-72">
        <Icon name="mdi:magnify" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted w-4 h-4" />
        <input v-model="q" @input="debouncedSearch" placeholder="Search..." class="input pl-9 py-1.5 text-sm" />
      </div>
    </div>

    <div v-if="pending" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 9" :key="i" class="card p-4 animate-pulse h-32"></div>
    </div>
    <div v-else-if="repos?.length === 0" class="text-center py-20 text-muted">
      <Icon name="mdi:source-repository-multiple" class="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p>No repositories found</p>
    </div>
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <RepoCard v-for="repo in repos" :key="repo.id" :repo="repo" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'
useSeoMeta({ title: 'Explore' })
const route = useRoute()
const q = ref((route.query.q as string) || '')
const { get } = useApi()
const { data: repos, pending, refresh } = await useAsyncData('explore', () =>
  get<Repo[]>(`/api/repos/?limit=30${q.value ? `&q=${encodeURIComponent(q.value)}` : ''}`)
)
const debouncedSearch = useDebounceFn(() => refresh(), 400)
</script>
