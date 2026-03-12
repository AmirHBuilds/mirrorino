<template>
  <div>
    <h1 class="text-xl font-bold mb-6">Dashboard</h1>
    <div v-if="pending" class="grid grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="card p-4 h-24 animate-pulse"></div>
    </div>
    <div v-else class="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      <div class="card p-5" v-for="stat in statCards" :key="stat.label">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-lg flex items-center justify-center" :class="stat.color">
            <Icon :name="stat.icon" class="w-5 h-5" />
          </div>
          <div>
            <p class="text-2xl font-bold font-mono">{{ stat.value }}</p>
            <p class="text-xs text-muted">{{ stat.label }}</p>
          </div>
        </div>
      </div>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card p-4">
        <h2 class="text-sm font-semibold mb-3">Quick Actions</h2>
        <div class="space-y-2">
          <NuxtLink to="/admin/verify" class="flex items-center justify-between p-3 rounded-md hover:bg-surface-2 transition-colors">
            <div class="flex items-center gap-2 text-sm"><Icon name="mdilocal:shield-check-outline" class="w-4 h-4 text-accent-2" /> Verification Queue</div>
            <span v-if="stats?.pending_verifications" class="text-xs bg-warning/20 text-warning px-2 py-0.5 rounded-full font-mono">{{ stats.pending_verifications }}</span>
          </NuxtLink>
          <NuxtLink to="/admin/users" class="flex items-center gap-2 p-3 rounded-md hover:bg-surface-2 transition-colors text-sm"><Icon name="mdilocal:account-group-outline" class="w-4 h-4 text-accent-2" /> Manage Users</NuxtLink>
          <NuxtLink to="/admin/statistics" class="flex items-center gap-2 p-3 rounded-md hover:bg-surface-2 transition-colors text-sm"><Icon name="mdilocal:chart-line" class="w-4 h-4 text-accent-2" /> View Statistics</NuxtLink>
          <NuxtLink to="/admin/repos" class="flex items-center gap-2 p-3 rounded-md hover:bg-surface-2 transition-colors text-sm"><Icon name="mdilocal:repo-clone" class="w-4 h-4 text-accent-2" /> Manage Repositories</NuxtLink>
          <NuxtLink to="/admin/ads" class="flex items-center gap-2 p-3 rounded-md hover:bg-surface-2 transition-colors text-sm"><Icon name="mdilocal:advertisements" class="w-4 h-4 text-accent-2" /> Manage Ads</NuxtLink>
        </div>
      </div>
      <div class="card p-4">
        <h2 class="text-sm font-semibold mb-3">Storage</h2>
        <div class="text-center py-4">
          <p class="text-3xl font-bold font-mono">{{ formatBytes(stats?.total_storage_bytes || 0) }}</p>
          <p class="text-xs text-muted mt-1">total stored across all repos</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatBytes } from '~/utils/format'
import type { AdminStats } from '~/types'
definePageMeta({ layout: 'admin', middleware: 'admin' })
useSeoMeta({ title: 'Admin Dashboard' })
const { get } = useApi()
const { data: stats, pending } = await useAsyncData(
  'admin-stats',
  () => get<AdminStats>('/api/admin/stats'),
  { server: false, default: () => null },
)
const statCards = computed(() => [
  { label: 'Total Users',   value: stats.value?.total_users || 0,     icon: 'mdilocal:account-group-outline', color: 'bg-accent-2/10 text-accent-2' },
  { label: 'Repositories',  value: stats.value?.total_repos || 0,     icon: 'mdilocal:repo-clone',     color: 'bg-success/10 text-success' },
  { label: 'Files',         value: stats.value?.total_files || 0,     icon: 'mdilocal:file-multiple-outline',  color: 'bg-accent/10 text-accent' },
  { label: 'Pending Review',value: stats.value?.pending_verifications || 0, icon: 'mdilocal:shield-check-outline', color: 'bg-warning/10 text-warning' },
  { label: 'Banned Users',  value: stats.value?.banned_users || 0,    icon: 'mdilocal:account-cancel-outline', color: 'bg-danger/10 text-danger' },
  { label: 'Storage Used',  value: formatBytes(stats.value?.total_storage_bytes || 0), icon: 'mdilocal:database-outline', color: 'bg-surface-3 text-fg' },
])
</script>
