<template>
  <div>
    <h1 class="text-xl font-bold mb-6">Verification Queue</h1>
    <div v-if="!repos?.length" class="card py-16 text-center text-muted text-sm">
      <Icon name="mdi:shield-check" class="w-10 h-10 mx-auto mb-3 text-success opacity-50" />
      All caught up — no pending verifications
    </div>
    <div v-else class="space-y-3">
      <div v-for="repo in repos" :key="repo.id" class="card p-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <NuxtLink :to="`/${repo.owner.username}/${repo.slug}`" class="font-medium text-accent-2 hover:underline text-sm">{{ repo.owner.username }}/{{ repo.name }}</NuxtLink>
            </div>
            <p v-if="repo.description" class="text-xs text-muted">{{ repo.description }}</p>
            <p v-if="repo.verification_note" class="text-xs text-muted mt-1 italic">"{{ repo.verification_note }}"</p>
            <p class="text-xs text-muted mt-1 font-mono">{{ repo.file_count }} files · {{ formatBytes(repo.total_size) }}</p>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button @click="action(repo.id, 'reject')" class="btn-danger text-xs py-1.5 px-3">Reject</button>
            <button @click="action(repo.id, 'approve')" class="btn-primary text-xs py-1.5 px-3">
              <Icon name="mdi:check" class="w-3.5 h-3.5" /> Approve
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatBytes } from '~/utils/format'
definePageMeta({ layout: 'admin', middleware: 'admin' })
useSeoMeta({ title: 'Verify Queue' })
const { get, post } = useApi()
const { data: repos, refresh } = await useAsyncData('verify-queue', () => get<any[]>('/api/admin/verify-queue'))
async function action(id: number, act: string) {
  await post(`/api/admin/repos/${id}/verify`, { action: act })
  await refresh()
}
</script>
