<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <NuxtLink to="/user/repos" class="flex items-center gap-1.5 text-sm text-muted hover:text-fg mb-6 transition-colors">
      <Icon name="mdi:arrow-left" class="w-4 h-4" /> Back to repositories
    </NuxtLink>

    <div v-if="repoId <= 0" class="card p-4 text-sm text-danger">Invalid repository id.</div>
    <template v-else>
      <h1 class="text-xl font-bold mb-2">Upload files</h1>
      <p class="text-sm text-muted mb-6">Repository ID: {{ repoId }}</p>
      <UploadZone :repo-id="repoId" @uploaded="onUploaded" />
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
useSeoMeta({ title: 'Upload Files' })

const route = useRoute()
const repoId = computed(() => Number(route.params.id || 0))

function onUploaded() {
  refreshNuxtData('my-repos')
}
</script>
