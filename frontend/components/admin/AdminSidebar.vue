<template>
  <aside class="w-56 shrink-0 border-r border-border min-h-screen pt-6 px-3">
    <p class="text-xs font-mono text-muted uppercase tracking-widest px-3 mb-3">Admin Panel</p>
    <nav class="flex flex-col gap-0.5">
      <NuxtLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors"
        :class="$route.path === item.to ? 'bg-surface-2 text-fg' : 'text-muted hover:text-fg hover:bg-surface-2'"
      >
        <Icon :name="item.icon" class="w-4 h-4 shrink-0" />
        {{ item.label }}
        <span v-if="item.badge" class="ml-auto text-xs bg-warning/20 text-warning px-1.5 py-0.5 rounded-full font-mono">{{ item.badge }}</span>
      </NuxtLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import type { AdminPermissions } from '~/types'

const { data: stats } = await useFetch('/api/admin/stats', {
  baseURL: useRuntimeConfig().public.apiBase,
  headers: computed(() => ({ Authorization: `Bearer ${localStorage.getItem('token')}` })),
  default: () => ({ pending_verifications: 0 }),
})

const { data: permissions } = await useFetch<AdminPermissions>('/api/admin/my-permissions', {
  baseURL: useRuntimeConfig().public.apiBase,
  headers: computed(() => ({ Authorization: `Bearer ${localStorage.getItem('token')}` })),
  default: () => ({ manage_users: false, manage_repos: false, manage_ads: false, view_stats: false }),
})

const nav = computed(() => {
  const items = [{ to: '/admin', icon: 'mdilocal:view-dashboard-outline', label: 'Dashboard' }]
  if (permissions.value?.view_stats) items.push({ to: '/admin/statistics', icon: 'mdilocal:chart-line', label: 'Statistics' })
  if (permissions.value?.manage_repos) {
    items.push({ to: '/admin/verify', icon: 'mdilocal:shield-check-outline', label: 'Verify Queue', badge: stats.value?.pending_verifications || undefined })
    items.push({ to: '/admin/repos', icon: 'mdilocal:source-repository', label: 'Repositories' })
  }
  if (permissions.value?.manage_users) items.push({ to: '/admin/users', icon: 'mdilocal:account-group-outline', label: 'Users' })
  if (permissions.value?.manage_ads) items.push({ to: '/admin/ads', icon: 'mdilocal:advertisements', label: 'Ads' })
  return items
})
</script>
