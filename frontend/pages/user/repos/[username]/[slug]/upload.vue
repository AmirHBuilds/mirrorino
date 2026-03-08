<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <NuxtLink to="/user/repos" class="flex items-center gap-1.5 text-sm text-muted hover:text-fg mb-6 transition-colors">
      <Icon name="mdi:arrow-left" class="w-4 h-4" /> Back to repositories
    </NuxtLink>

    <div v-if="!repo" class="card p-4 text-sm text-danger">Repository not found.</div>
    <template v-else>
      <h1 class="text-xl font-bold mb-2">Upload files</h1>
      <p class="text-sm text-muted mb-6">Repository: {{ repo.owner.username }}/{{ repo.name }}</p>
      <UploadZone :repo-username="repo.owner.username" :repo-slug="repo.slug" @uploaded="onUploaded" />
    </template>
  </div>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'

definePageMeta({ middleware: 'auth' })
useSeoMeta({ title: 'Upload Files' })

const route = useRoute()
const { get } = useApi()

const username = computed(() => String(route.params.username || ''))
const slug = computed(() => String(route.params.slug || ''))

const { data: repo } = await useAsyncData(
  'upload-repo-by-identity',
  async () => {
    if (!username.value || !slug.value) return null
    const repos = await get<Repo[]>('/api/repos/mine')
    return repos.find((entry) => entry.owner.username === username.value && entry.slug === slug.value) || null
  },
  { watch: [username, slug] },
)

function onUploaded() {
  refreshNuxtData('my-repos')
}
</script>
