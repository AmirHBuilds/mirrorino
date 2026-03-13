<template>
  <NuxtLink :to="`/${repo.owner.username}/${repo.slug}`" class="card p-4 hover:border-surface-3 transition-colors block">
    <!-- Header -->
    <div class="flex items-start justify-between gap-2 mb-2">
      <div class="flex items-center gap-2 min-w-0">
        <Icon name="mdilocal:repo-clone" class="w-4 h-4 text-accent-2 shrink-0" />
        <span class="font-medium text-sm truncate">
          <button class="text-muted hover:underline" @click.stop.prevent="navigateTo(`/${repo.owner.username}/repos`)">{{ repo.owner.username }}</button>
          <span class="text-muted">/</span>
          <span class="text-accent-2">{{ repo.name }}</span>
        </span>
      </div>
      <VerificationBadge :status="displayStatus" />
    </div>

    <!-- Description -->
    <p v-if="repo.description" class="text-xs text-muted line-clamp-2 mb-3">{{ repo.description }}</p>
    <p v-else class="text-xs text-surface-3 italic mb-3">No description</p>

    <!-- Warning banner for unverified -->
    <div v-if="displayStatus === 'rejected'" class="flex items-center gap-1.5 text-xs text-danger bg-danger/5 border border-danger/30 rounded px-2 py-1.5 mb-3">
      <Icon name="mdilocal:alert-circle" class="w-3.5 h-3.5 shrink-0" />
      Marked as spam
    </div>
    <div v-else-if="displayStatus === 'unverified'" class="flex items-center gap-1.5 text-xs text-warning bg-warning/5 border border-warning/20 rounded px-2 py-1.5 mb-3">
      <Icon name="mdilocal:alert-outline" class="w-3.5 h-3.5 shrink-0" />
      Download at your own risk — unverified repository
    </div>

    <MirrorSourceBox :repo="repo" compact class="mb-2" />

    <!-- Stats -->
    <div class="flex items-center gap-4 text-xs text-muted font-mono">
      <span class="flex items-center gap-1"><Icon name="mdilocal:file-multiple-outline" class="w-3.5 h-3.5" />{{ repo.file_count }} files</span>
      <span class="flex items-center gap-1"><Icon name="mdilocal:download-outline" class="w-3.5 h-3.5" />{{ repo.download_count.toLocaleString() }}</span>
      <span class="hidden sm:flex items-center gap-1"><Icon name="mdilocal:repo-clone" class="w-3.5 h-3.5" />{{ repo.clone_count.toLocaleString() }}</span>
      <span class="flex items-center gap-1"><Icon name="mdilocal:database-outline" class="w-3.5 h-3.5" />{{ formatBytes(repo.total_size) }}</span>
      <span class="ml-auto flex items-center gap-1"><Icon name="mdilocal:clock-outline" class="w-3.5 h-3.5" />{{ formatRelative(repo.created_at) }}</span>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import { formatBytes, formatRelative } from '~/utils/format'
import type { Repo } from '~/types'
import { visibleVerificationStatus } from '~/utils/repo'

const props = defineProps<{ repo: Repo }>()
const { user } = useAuth()
const isOwner = computed(() => user.value?.id === props.repo.owner.id)
const displayStatus = computed(() => visibleVerificationStatus(props.repo.verification_status, !!isOwner.value))
</script>
