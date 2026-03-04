<template>
  <div class="max-w-2xl mx-auto px-4 py-8">
    <h1 class="text-xl font-bold mb-6">Settings</h1>
    <div class="space-y-6">
      <!-- Profile -->
      <div class="card p-5">
        <h2 class="text-sm font-semibold mb-4">Account</h2>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-muted block mb-1.5">Username</label>
            <input :value="user?.username" class="input opacity-60" disabled />
            <p class="text-xs text-muted mt-1">Username cannot be changed</p>
          </div>
          <div>
            <label class="text-xs text-muted block mb-1.5">Email</label>
            <input v-model="form.email" class="input" type="email" />
          </div>
          <div>
            <label class="text-xs text-muted block mb-1.5">New password</label>
            <input v-model="form.password" class="input" type="password" placeholder="Leave blank to keep current" />
          </div>
          <p v-if="msg" class="text-xs" :class="msgOk ? 'text-success' : 'text-danger'">{{ msg }}</p>
          <button @click="save" class="btn-primary text-sm py-1.5" :disabled="saving">
            <Icon v-if="saving" name="mdi:loading" class="w-4 h-4 animate-spin" />
            Save changes
          </button>
        </div>
      </div>

      <!-- Storage -->
      <div class="card p-5" v-if="user">
        <h2 class="text-sm font-semibold mb-4">Storage</h2>
        <StorageBar :used="user.storage_used" :limit="user.storage_limit" />
        <div class="mt-4 p-3 bg-surface-2 rounded-md text-xs text-muted">
          <p class="font-medium text-fg mb-1">Need more space?</p>
          <p>Request verification for a public-good repository to get up to 2GB. Or contact the admin to upgrade your plan.</p>
        </div>
      </div>

      <!-- Danger zone -->
      <div class="card p-5 border-danger/20">
        <h2 class="text-sm font-semibold text-danger mb-4">Danger zone</h2>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm">Delete account</p>
            <p class="text-xs text-muted">Permanently delete your account, all repositories, and files.</p>
          </div>
          <button @click="deleteAccount" class="btn-danger text-sm py-1.5">Delete account</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
useSeoMeta({ title: 'Settings' })
const { user, logout } = useAuth()
const { put, delete: del } = useApi()
const form   = reactive({ email: user.value?.email || '', password: '' })
const saving = ref(false)
const msg    = ref('')
const msgOk  = ref(false)

async function save() {
  saving.value = true
  msg.value = ''
  try {
    const payload: Record<string, string> = {}
    if (form.email !== user.value?.email) payload.email = form.email
    if (form.password) payload.password = form.password
    await put('/api/users/me', payload)
    msg.value = 'Changes saved successfully'
    msgOk.value = true
    form.password = ''
  } catch (e: any) {
    msg.value = e.message
    msgOk.value = false
  } finally {
    saving.value = false
  }
}

async function deleteAccount() {
  if (!confirm('This will permanently delete your account and all data. Are you sure?')) return
  await del('/api/users/me')
  logout()
}
</script>
