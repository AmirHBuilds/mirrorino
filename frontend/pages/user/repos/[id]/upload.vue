<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <NuxtLink to="/user/repos" class="flex items-center gap-1.5 text-sm text-muted hover:text-fg mb-6 transition-colors">
      <Icon name="mdi:arrow-left" class="w-4 h-4" /> Back to repositories
    </NuxtLink>
    <h1 class="text-xl font-bold mb-6">Upload files</h1>
    <UploadZone :repo-id="Number($route.params.id)" @uploaded="onUploaded" />
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
useSeoMeta({ title: 'Upload Files' })
function onUploaded() { refreshNuxtData('my-repos') }
</script>
