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
              <th class="text-left px-4 py-3 hidden md:table-cell">Role</th>
              <th class="text-left px-4 py-3 hidden lg:table-cell">Storage</th>
              <th class="text-left px-4 py-3">Status</th>
              <th class="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr v-for="u in users" :key="u.id" class="hover:bg-surface-2/40 transition-colors" :class="u.is_banned ? 'opacity-70' : ''">
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 rounded-full bg-surface-2 border border-border flex items-center justify-center text-xs font-mono">{{ u.username[0].toUpperCase() }}</div>
                  <div>
                    <p class="font-medium text-sm">{{ u.username }}</p>
                    <p class="text-xs text-muted">{{ u.email }}</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3 hidden md:table-cell">
                <span class="text-xs font-mono px-2 py-0.5 rounded border" :class="roleClass(u.role)">{{ u.role }}</span>
              </td>
              <td class="px-4 py-3 hidden lg:table-cell text-xs text-muted font-mono">{{ formatBytes(u.storage_used) }} / {{ formatBytes(u.storage_limit) }}</td>
              <td class="px-4 py-3">
                <span class="text-xs px-2 py-0.5 rounded-full border" :class="u.is_banned ? 'text-danger border-danger/30' : 'text-success border-success/30'">{{ u.is_banned ? 'Banned' : 'Active' }}</span>
              </td>
              <td class="px-4 py-3 text-right">
                <button class="btn-ghost text-xs py-1 px-2" @click="openUserMenu(u)">
                  <Icon name="mdilocal:dots-vertical" class="w-4 h-4" />
                  Manage
                </button>
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

    <div v-if="selectedUser" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4" @click.self="selectedUser = null">
      <div class="card p-6 w-full max-w-xl">
        <div class="flex items-start justify-between gap-3 mb-5">
          <div>
            <h2 class="text-lg font-semibold">Manage {{ selectedUser.username }}</h2>
            <p class="text-xs text-muted mt-1">{{ selectedUser.email }}</p>
          </div>
          <button class="btn-ghost py-1 px-2" @click="selectedUser = null"><Icon name="mdilocal:close" class="w-4 h-4" /></button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label class="text-xs text-muted">Role</label>
            <select v-model="editDraft.role" class="input py-2 text-sm">
              <option value="user">user</option>
              <option value="moderator">moderator</option>
              <option value="admin">admin</option>
              <option value="superadmin">superadmin</option>
            </select>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs text-muted">Plan ID</label>
            <input v-model.number="editDraft.plan_id" type="number" min="1" class="input py-2 text-sm" />
          </div>

          <div class="space-y-1.5 md:col-span-2">
            <label class="text-xs text-muted">Storage Limit (GB)</label>
            <input v-model.number="editDraft.storage_gb" type="number" min="1" class="input py-2 text-sm" />
          </div>
        </div>

        <div class="mt-5 p-3 rounded-md bg-surface-2 text-xs text-muted font-mono">
          Used: {{ formatBytes(selectedUser.storage_used) }} / Current Limit: {{ formatBytes(selectedUser.storage_limit) }}
        </div>

        <div class="flex flex-wrap gap-2 pt-5">
          <button class="btn-primary text-sm" @click="saveUserEdits">Save Changes</button>
          <button class="btn-ghost text-sm" :class="selectedUser.is_banned ? 'text-success' : 'text-warning'" @click="toggleBan(selectedUser)">{{ selectedUser.is_banned ? 'Unban User' : 'Ban User' }}</button>
          <button class="btn-ghost text-sm text-danger ml-auto" @click="deleteUser(selectedUser.id)">Delete User</button>
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
const selectedUser = ref<User | null>(null)
const permDraft = reactive<Record<number, AdminPermissions>>({})
const editDraft = reactive({
  role: 'user' as User['role'],
  storage_gb: 1,
  plan_id: 1,
})

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
  admins,
  (value) => {
    for (const admin of value || []) {
      permDraft[admin.id] = { ...admin.permissions }
    }
  },
  { immediate: true },
)

function roleClass(role: User['role']) {
  if (role === 'superadmin') return 'text-accent border-accent/30'
  if (role === 'admin') return 'text-accent-2 border-accent-2/30'
  if (role === 'moderator') return 'text-warning border-warning/30'
  return 'text-muted border-border'
}

function openUserMenu(user: User) {
  selectedUser.value = user
  editDraft.role = user.role
  editDraft.storage_gb = Math.max(1, Math.round(user.storage_limit / 1024 ** 3))
  editDraft.plan_id = 1
}

async function toggleBan(u: User) {
  await put(`/api/admin/users/${u.id}`, { is_banned: !u.is_banned })
  await refresh()
  if (selectedUser.value?.id === u.id) {
    selectedUser.value = users.value?.find((item) => item.id === u.id) || null
  }
}

async function saveUserEdits() {
  if (!selectedUser.value) return
  const storageGb = Number(editDraft.storage_gb || 0)
  const planId = Number(editDraft.plan_id || 0)
  await put(`/api/admin/users/${selectedUser.value.id}`, {
    role: editDraft.role,
    storage_limit: Math.max(1, Math.round(storageGb)) * 1024 ** 3,
    plan_id: Math.max(1, Math.round(planId)),
  })
  await refresh()
  selectedUser.value = users.value?.find((item) => item.id === selectedUser.value?.id) || null
}

async function deleteUser(id: number) {
  if (!confirm('Permanently delete this user and all their data?')) return
  await del(`/api/admin/users/${id}`)
  selectedUser.value = null
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
