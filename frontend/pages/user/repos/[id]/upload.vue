<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <div class="card p-4 text-sm text-muted">Redirecting to repository upload page…</div>
  </div>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const { get } = useApi()
const repoId = computed(() => Number(route.params.id || 0))

await useAsyncData('upload-repo-legacy-redirect', async () => {
  if (repoId.value <= 0) {
    await navigateTo('/user/repos')
    return null
  }

  const repos = await get<Repo[]>('/api/repos/mine')
  const repo = repos.find((entry) => entry.id === repoId.value)
  if (!repo) {
    await navigateTo('/user/repos')
    return null
  }

  await navigateTo(`/user/repos/${repo.owner.username}/${repo.slug}/upload`, { replace: true })
  return null
}, { server: false })
</script>
