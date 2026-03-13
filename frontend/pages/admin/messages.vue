<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold">User Messages</h1>
        <p class="text-sm text-muted">Publish clear notices for all users or one specific user.</p>
      </div>
      <button class="btn-primary" @click="openCreate">New Message</button>
    </div>

    <div class="grid gap-4">
      <article v-for="message in messages" :key="message.id" class="card p-5">
        <div class="flex flex-col lg:flex-row lg:items-start gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex flex-wrap items-center gap-2 mb-2">
              <h2 class="font-semibold text-base">{{ message.title }}</h2>
              <span class="text-xs px-2 py-0.5 rounded-full border" :class="message.is_active ? 'border-success/30 text-success' : 'border-border text-muted'">{{ message.is_active ? 'Active' : 'Inactive' }}</span>
              <span class="text-xs px-2 py-0.5 rounded-full border border-accent/30 text-accent">
                {{ message.recipient_user_id ? `Target: ${message.recipient_username || `#${message.recipient_user_id}`}` : 'Target: All users' }}
              </span>
            </div>
            <p class="text-sm text-muted whitespace-pre-wrap">{{ message.body }}</p>
            <div class="mt-3 text-xs text-muted font-mono flex flex-wrap gap-4">
              <span>Seen: {{ message.acknowledged_users }}</span>
              <span>Pending: {{ message.pending_users }}</span>
            </div>
          </div>
          <div class="flex lg:flex-col gap-2">
            <button class="btn-ghost text-sm" @click="startEdit(message)">Edit</button>
            <button class="btn-ghost text-sm" @click="toggleActive(message)">{{ message.is_active ? 'Deactivate' : 'Activate' }}</button>
            <button class="btn-ghost text-sm text-danger" @click="remove(message.id)">Delete</button>
          </div>
        </div>
      </article>

      <p v-if="!messages.length" class="card p-6 text-sm text-muted">No user messages yet.</p>
    </div>

    <div v-if="showModal" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center px-4" @click.self="showModal = false">
      <div class="card p-6 w-full max-w-2xl space-y-4">
        <h2 class="text-lg font-semibold">{{ editingId ? 'Edit message' : 'Create message' }}</h2>
        <input v-model="form.title" class="input" placeholder="Message title" />
        <textarea v-model="form.body" class="input min-h-[140px]" placeholder="Explain the message clearly" />

        <div class="space-y-1">
          <label class="text-sm text-muted">Send to</label>
          <select v-model.number="form.recipient_user_id" class="input py-2 text-sm">
            <option :value="0">All users</option>
            <option v-for="user in users" :key="user.id" :value="user.id">{{ user.username }} ({{ user.email }})</option>
          </select>
        </div>

        <label class="flex items-center gap-2 text-sm text-muted"><input v-model="form.is_active" type="checkbox" /> Active</label>
        <div class="flex gap-2 justify-end">
          <button class="btn-secondary" @click="showModal = false">Cancel</button>
          <button class="btn-primary" @click="save">{{ editingId ? 'Save' : 'Create' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AdminUserMessage, User } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin' })
useSeoMeta({ title: 'Admin · User Messages' })

const { get, post, put, delete: del } = useApi()
const showModal = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ title: '', body: '', is_active: true, recipient_user_id: 0 })

const { data: users } = await useAsyncData('admin-users-for-messages', () => get<User[]>('/api/admin/users?limit=100'), {
  server: false,
  default: () => [],
})

const { data: messages, refresh } = await useAsyncData('admin-user-messages', () => get<AdminUserMessage[]>('/api/admin/user-messages'), {
  server: false,
  default: () => [],
})

function openCreate() {
  editingId.value = null
  form.title = ''
  form.body = ''
  form.is_active = true
  form.recipient_user_id = 0
  showModal.value = true
}

function startEdit(message: AdminUserMessage) {
  editingId.value = message.id
  form.title = message.title
  form.body = message.body
  form.is_active = message.is_active
  form.recipient_user_id = message.recipient_user_id || 0
  showModal.value = true
}

async function save() {
  const payload = {
    title: form.title,
    body: form.body,
    is_active: form.is_active,
    recipient_user_id: form.recipient_user_id,
  }
  if (editingId.value) await put(`/api/admin/user-messages/${editingId.value}`, payload)
  else await post('/api/admin/user-messages', payload)
  showModal.value = false
  await refresh()
}

async function toggleActive(message: AdminUserMessage) {
  await put(`/api/admin/user-messages/${message.id}`, { is_active: !message.is_active })
  await refresh()
}

async function remove(id: number) {
  if (!confirm('Delete this user message?')) return
  await del(`/api/admin/user-messages/${id}`)
  await refresh()
}
</script>
