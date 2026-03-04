<template>
  <div class="min-h-[80vh] flex items-center justify-center px-4 py-10">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <span class="text-4xl text-accent font-mono">▼</span>
        <h1 class="text-2xl font-bold mt-3">Create account</h1>
      </div>
      <div class="card p-6">
        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="text-xs text-muted block mb-1.5">Username</label>
            <input v-model="form.username" class="input" placeholder="cool_username" required />
            <p class="text-xs text-muted mt-1">Letters, numbers, underscore. 3–50 chars.</p>
          </div>
          <div>
            <label class="text-xs text-muted block mb-1.5">Email</label>
            <input v-model="form.email" type="email" class="input" placeholder="you@example.com" required />
          </div>
          <div>
            <label class="text-xs text-muted block mb-1.5">Password</label>
            <input v-model="form.password" type="password" class="input" placeholder="Min 8 characters" required />
          </div>
          <div>
            <label class="text-xs text-muted block mb-1.5">CAPTCHA</label>
            <div class="flex gap-2 items-center mb-2">
              <img v-if="captcha" :src="captcha.image_base64" class="h-12 rounded border border-border bg-white" />
              <div v-else class="h-12 w-48 bg-surface-2 animate-pulse rounded"></div>
              <button type="button" @click="loadCaptcha" class="btn-ghost py-1 px-2"><Icon name="mdi:refresh" class="w-4 h-4" /></button>
            </div>
            <input v-model="form.captcha_answer" class="input" placeholder="Enter the text above" required />
          </div>
          <p v-if="error" class="text-xs text-danger">{{ error }}</p>
          <button type="submit" class="btn-primary w-full justify-center py-2.5" :disabled="loading">
            <Icon v-if="loading" name="mdi:loading" class="w-4 h-4 animate-spin" />
            {{ loading ? 'Creating account...' : 'Create account' }}
          </button>
        </form>
      </div>
      <p class="text-center text-sm text-muted mt-4">
        Already have one? <NuxtLink to="/login" class="text-accent-2 hover:underline">Sign in</NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
useSeoMeta({ title: 'Sign up' })
const { get, post } = useApi()
const form    = reactive({ username: '', email: '', password: '', captcha_id: '', captcha_answer: '' })
const captcha = ref<{ captcha_id: string; image_base64: string } | null>(null)
const error   = ref('')
const loading = ref(false)

async function loadCaptcha() {
  captcha.value = await get('/api/auth/captcha')
  form.captcha_id = captcha.value!.captcha_id
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await post('/api/auth/register', { ...form })
    navigateTo('/login')
  } catch (e: any) {
    error.value = e.message
    await loadCaptcha()
  } finally {
    loading.value = false
  }
}
onMounted(loadCaptcha)
</script>
