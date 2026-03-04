<template>
  <aside class="w-56 shrink-0 border-r border-border min-h-screen pt-6 px-3">
    <p class="text-xs font-mono text-muted uppercase tracking-widest px-3 mb-3">Admin Panel</p>
    <nav class="flex flex-col gap-0.5">
      <NuxtLink v-for="item in nav" :key="item.to" :to="item.to"
        class="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors"
        :class="$route.path === item.to ? 'bg-surface-2 text-fg' : 'text-muted hover:text-fg hover:bg-surface-2'">
        <Icon :name="item.icon" class="w-4 h-4 shrink-0" />
        {{ item.label }}
        <span v-if="item.badge" class="ml-auto text-xs bg-warning/20 text-warning px-1.5 py-0.5 rounded-full font-mono">{{ item.badge }}</span>
      </NuxtLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
const { data: stats } = await useFetch('/api/admin/stats', {
  baseURL: useRuntimeConfig().public.apiBase,
  headers: computed(() => ({ Authorization: `Bearer ${localStorage.getItem('token')}` })),
  default: () => ({ pending_verifications: 0 }),
})

const nav = computed(() => [
  { to: '/admin', icon: 'mdi:view-dashboard-outline', label: 'Dashboard' },
  { to: '/admin/verify', icon: 'mdi:shield-check-outline', label: 'Verify Queue', badge: stats.value?.pending_verifications || undefined },
  { to: '/admin/users', icon: 'mdi:account-group-outline', label: 'Users' },
  { to: '/admin/repos', icon: 'mdi:source-repository', label: 'Repositories' },
  { to: '/admin/ads', icon: 'mdi:advertisements', label: 'Ads' },
])
</script>
