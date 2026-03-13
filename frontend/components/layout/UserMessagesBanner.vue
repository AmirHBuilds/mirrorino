<template>
  <section v-if="current" class="border-b border-border bg-gradient-to-r from-accent/20 via-accent-2/10 to-warning/20">
    <div class="max-w-7xl mx-auto px-4 py-4 sm:py-5">
      <div class="rounded-xl border border-accent/30 bg-surface/95 shadow-sm p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-4">
        <div class="flex-1 min-w-0">
          <p class="text-xs font-mono uppercase tracking-[0.18em] text-accent mb-2">Important message</p>
          <h3 class="text-base sm:text-lg font-semibold leading-tight">{{ current.title }}</h3>
          <p class="text-sm text-muted mt-1 whitespace-pre-wrap">{{ current.body }}</p>
        </div>
        <button class="btn-primary shrink-0" :disabled="submitting" @click="acknowledge(current.id)">
          {{ submitting ? 'Saving...' : 'Understand' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
interface ActiveUserMessage {
  id: number
  title: string
  body: string
  is_active: boolean
  created_by: number | null
  created_at: string
  updated_at: string
  acknowledged: boolean
}

const { isLoggedIn } = useAuth()
const { get, post } = useApi()
const messages = ref<ActiveUserMessage[]>([])
const submitting = ref(false)

const current = computed(() => messages.value.find((item) => !item.acknowledged))

async function loadMessages() {
  if (!isLoggedIn.value) {
    messages.value = []
    return
  }
  messages.value = await get<ActiveUserMessage[]>('/api/users/me/messages')
}

async function acknowledge(messageId: number) {
  if (submitting.value) return
  submitting.value = true
  try {
    await post(`/api/users/me/messages/${messageId}/acknowledge`)
    const item = messages.value.find((entry) => entry.id === messageId)
    if (item) item.acknowledged = true
  } finally {
    submitting.value = false
  }
}

watch(isLoggedIn, () => {
  loadMessages()
}, { immediate: true })
</script>
