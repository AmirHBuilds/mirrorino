<template>
  <div class="space-y-8">
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h1 class="text-xl font-bold">Users</h1>
        <div class="relative w-full sm:w-72">
          <Icon name="mdilocal:magnify" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted w-4 h-4" />
          <input v-model="q" @input="debouncedRefresh" placeholder="Search users..." class="input pl-9 py-1.5 text-sm" />
        </div>
      </div>
      <div class="card overflow-hidden">
        <table class="w-full text-sm">
          <thead class="border-b border-border">
            <tr class="text-xs text-muted font-mono">
              <th class="text-left px-4 py-3">User</th>
              <th class="text-left px-4 py-3">Role</th>
              <th class="text-left px-4 py-3 hidden md:table-cell">Storage</th>
              <th class="text-left px-4 py-3 hidden lg:table-cell">Plan</th>
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
              <td class="px-4 py-3">
                <select v-model="roleDraft[u.id]" class="input py-1 px-2 text-xs w-28" @change="setRole(u.id)">
                  <option value="user">user</option>
                  <option value="moderator">moderator</option>
                  <option value="admin">admin</option>
                  <option value="superadmin">superadmin</option>
                </select>
              </td>
              <td class="px-4 py-3 hidden md:table-cell">
                <div class="text-xs font-mono text-muted mb-2">{{ formatBytes(u.storage_used) }} / {{ formatBytes(u.storage_limit) }}</div>
                <div class="flex items-center gap-1.5">
                  <input v-model.number="storageDraft[u.id]" type="number" min="1" step="1" class="input py-1 px-2 text-xs w-20" />
                  <span class="text-xs text-muted">GB</span>
                  <button @click="setStorage(u.id)" class="btn-ghost py-1 px-2 text-xs">Set</button>
                </div>
              </td>
              <td class="px-4 py-3 hidden lg:table-cell">
                <div class="flex items-center gap-1.5">
                  <input v-model.number="planDraft[u.id]" type="number" min="1" step="1" class="input py-1 px-2 text-xs w-20" />
                  <button @click="setPlan(u.id)" class="btn-ghost py-1 px-2 text-xs">Set</button>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-1 justify-end">
                  <button @click="toggleBan(u)" class="btn-ghost py-1 px-2 text-xs" :class="u.is_banned ? 'text-success' : 'text-warning'">{{ u.is_banned ? 'Unban' : 'Ban' }}</button>
                  <button @click="deleteUser(u.id)" class="btn-ghost py-1 px-2 text-xs text-danger"><Icon name="mdilocal:trash-can-outline" class="w-3.5 h-3.5" /></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card p-5">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">Admin Accounts & Permissions</h2>
        <button class="btn-primary text-sm py-1.5" @click="showCreate = true">Create Admin</button>
      </div>
      <div class="space-y-3">
        <div v-for="admin in admins" :key="admin.id" class="border border-border rounded-lg p-3">
          <div class="flex items-center justify-between gap-3 mb-2">
            <div>
              <p class="font-medium">{{ admin.username }}</p>
              <p class="text-xs text-muted">{{ admin.email }} · {{ admin.role }}</p>
            </div>
            <button v-if="admin.role !== 'superadmin'" class="btn-ghost text-xs" @click="savePermissions(admin)">Save Permissions</button>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <label class="flex items-center gap-2"><input type="checkbox" v-model="permDraft[admin.id].manage_users" :disabled="admin.role === 'superadmin'" /> Manage Users</label>
            <label class="flex items-center gap-2"><input type="checkbox" v-model="permDraft[admin.id].manage_repos" :disabled="admin.role === 'superadmin'" /> Manage Repositories</label>
            <label class="flex items-center gap-2"><input type="checkbox" v-model="permDraft[admin.id].manage_ads" :disabled="admin.role === 'superadmin'" /> Manage Ads</label>
            <label class="flex items-center gap-2"><input type="checkbox" v-model="permDraft[admin.id].view_stats" :disabled="admin.role === 'superadmin'" /> View Stats</label>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCreate" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4" @click.self="showCreate = false">
      <div class="card p-6 w-full max-w-lg">
        <h2 class="text-lg font-semibold mb-4">Create Admin</h2>
        <div class="space-y-3">
          <input v-model="newAdmin.username" placeholder="username" class="input" />
          <input v-model="newAdmin.email" placeholder="email" class="input" />
          <input v-model="newAdmin.password" type="password" placeholder="password" class="input" />
          <div class="grid grid-cols-2 gap-2 text-xs">
            <label class="flex items-center gap-2"><input type="checkbox" v-model="newAdmin.permissions.manage_users" /> Manage Users</label>
            <label class="flex items-center gap-2"><input type="checkbox" v-model="newAdmin.permissions.manage_repos" /> Manage Repositories</label>
            <label class="flex items-center gap-2"><input type="checkbox" v-model="newAdmin.permissions.manage_ads" /> Manage Ads</label>
            <label class="flex items-center gap-2"><input type="checkbox" v-model="newAdmin.permissions.view_stats" /> View Stats</label>
          </div>
          <div class="flex gap-2 pt-2">
            <button @click="showCreate = false" class="btn-secondary flex-1 justify-center">Cancel</button>
            <button @click="createAdmin" class="btn-primary flex-1 justify-center">Create</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatBytes } from '~/utils/format'
import type { AdminAccount, AdminPermissions, User } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin' })
useSeoMeta({ title: 'Admin · Users' })
const { get, post, put, delete: del } = useApi()

const q = ref('')
const showCreate = ref(false)
const storageDraft = reactive<Record<number, number>>({})
const roleDraft = reactive<Record<number, User['role']>>({})
const planDraft = reactive<Record<number, number>>({})
const permDraft = reactive<Record<number, AdminPermissions>>({})

const newAdmin = reactive({
  username: '',
  email: '',
  password: '',
  permissions: { manage_users: true, manage_repos: true, manage_ads: false, view_stats: true },
})

const { data: users, refresh } = await useAsyncData(
  () => `admin-users:${q.value}`,
  () => get<User[]>(`/api/admin/users${q.value ? `?q=${q.value}` : ''}`),
  { server: false, default: () => [] },
)

const { data: admins, refresh: refreshAdmins } = await useAsyncData('admin-accounts', () => get<AdminAccount[]>('/api/admin/admins'), {
  server: false,
  default: () => [],
})

const debouncedRefresh = useDebounceFn(() => refresh(), 400)

watch(
  users,
  (value) => {
    for (const user of value || []) {
      storageDraft[user.id] = Math.max(1, Math.round(user.storage_limit / 1024 ** 3))
      roleDraft[user.id] = user.role
      planDraft[user.id] = 1
    }
  },
  { immediate: true },
)

watch(
  admins,
  (value) => {
    for (const admin of value || []) {
      permDraft[admin.id] = { ...admin.permissions }
    }
  },
  { immediate: true },
)

async function toggleBan(u: User) {
  await put(`/api/admin/users/${u.id}`, { is_banned: !u.is_banned })
  await refresh()
}

async function setStorage(userId: number) {
  const gb = Number(storageDraft[userId] || 0)
  if (!Number.isFinite(gb) || gb < 1) return
  await put(`/api/admin/users/${userId}`, { storage_limit: Math.round(gb * 1024 ** 3) })
  await refresh()
}

async function setRole(userId: number) {
  await put(`/api/admin/users/${userId}`, { role: roleDraft[userId] })
  await refresh()
}

async function setPlan(userId: number) {
  const planId = Number(planDraft[userId] || 0)
  if (!Number.isFinite(planId) || planId < 1) return
  await put(`/api/admin/users/${userId}`, { plan_id: planId })
  await refresh()
}

async function deleteUser(id: number) {
  if (!confirm('Permanently delete this user and all their data?')) return
  await del(`/api/admin/users/${id}`)
  await refresh()
}

async function createAdmin() {
  await post('/api/admin/admins', {
    username: newAdmin.username,
    email: newAdmin.email,
    password: newAdmin.password,
    permissions: { ...newAdmin.permissions },
  })
  showCreate.value = false
  newAdmin.username = ''
  newAdmin.email = ''
  newAdmin.password = ''
  await refreshAdmins()
}

async function savePermissions(admin: AdminAccount) {
  await put(`/api/admin/admins/${admin.id}/permissions`, { ...permDraft[admin.id] })
  await refreshAdmins()
}
</script>
