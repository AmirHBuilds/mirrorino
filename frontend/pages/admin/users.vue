<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold">Users</h1>
      <div class="relative w-64">
        <Icon name="mdi:magnify" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted w-4 h-4" />
        <input v-model="q" @input="debouncedRefresh" placeholder="Search users..." class="input pl-9 py-1.5 text-sm" />
      </div>
    </div>
    <div class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead class="border-b border-border">
          <tr class="text-xs text-muted font-mono">
            <th class="text-left px-4 py-3">User</th>
            <th class="text-left px-4 py-3 hidden sm:table-cell">Role</th>
            <th class="text-left px-4 py-3 hidden md:table-cell">Storage</th>
            <th class="text-left px-4 py-3 hidden lg:table-cell">Joined</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          <tr v-for="u in users" :key="u.id" class="hover:bg-surface-2/40 transition-colors" :class="u.is_banned ? 'opacity-50' : ''">
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <div class="w-7 h-7 rounded-full bg-surface-2 border border-border flex items-center justify-center text-xs font-mono">{{ u.username[0].toUpperCase() }}</div>
                <div>
                  <p class="font-medium text-sm">{{ u.username }}</p>
                  <p class="text-xs text-muted">{{ u.email }}</p>
                </div>
              </div>
            </td>
            <td class="px-4 py-3 hidden sm:table-cell">
              <span class="text-xs font-mono px-2 py-0.5 rounded border border-border" :class="u.role === 'superadmin' ? 'text-accent border-accent/30' : u.role === 'admin' ? 'text-accent-2 border-accent-2/30' : 'text-muted'">{{ u.role }}</span>
            </td>
            <td class="px-4 py-3 hidden md:table-cell">
              <div class="text-xs font-mono text-muted">{{ formatBytes(u.storage_used) }} / {{ formatBytes(u.storage_limit) }}</div>
            </td>
            <td class="px-4 py-3 hidden lg:table-cell text-xs text-muted font-mono">{{ formatDate(u.created_at) }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-1 justify-end">
                <button @click="toggleBan(u)" class="btn-ghost py-1 px-2 text-xs" :class="u.is_banned ? 'text-success' : 'text-warning'">
                  {{ u.is_banned ? 'Unban' : 'Ban' }}
                </button>
                <button @click="deleteUser(u.id)" class="btn-ghost py-1 px-2 text-xs text-danger">
                  <Icon name="mdi:trash-can-outline" class="w-3.5 h-3.5" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatBytes, formatDate } from '~/utils/format'
import type { User } from '~/types'
definePageMeta({ layout: 'admin', middleware: 'admin' })
useSeoMeta({ title: 'Admin · Users' })
const { get, put, delete: del } = useApi()
const q = ref('')
const { data: users, refresh } = await useAsyncData('admin-users', () => get<User[]>(`/api/admin/users${q.value ? `?q=${q.value}` : ''}`))
const debouncedRefresh = useDebounceFn(() => refresh(), 400)
async function toggleBan(u: User) {
  await put(`/api/admin/users/${u.id}`, { is_banned: !u.is_banned })
  await refresh()
}
async function deleteUser(id: number) {
  if (!confirm('Permanently delete this user and all their data?')) return
  await del(`/api/admin/users/${id}`)
  await refresh()
}
</script>
