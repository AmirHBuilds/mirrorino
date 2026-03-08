<template>
  <div class="max-w-3xl mx-auto px-4 py-10">
    <h1 class="text-2xl font-bold mb-2">Contact Support</h1>
    <p class="text-sm text-muted mb-6">For private repositories and special plans, contact our support team.</p>

    <div class="card p-5 space-y-4 text-sm">
      <div class="flex items-center gap-2">
        <Icon name="mdi:email-outline" class="w-4 h-4 text-accent-2" />
        <span class="text-muted">Email:</span>
        <a v-if="email" :href="`mailto:${email}`" class="text-accent-2 hover:underline">{{ email }}</a>
        <span v-else class="text-muted">Not configured</span>
      </div>

      <div class="flex items-center gap-2">
        <Icon name="mdi:telegram" class="w-4 h-4 text-accent-2" />
        <span class="text-muted">Telegram ID:</span>
        <span v-if="telegramId">{{ telegramId }}</span>
        <span v-else class="text-muted">Not configured</span>
      </div>

      <div class="flex items-center gap-2">
        <Icon name="mdi:web" class="w-4 h-4 text-accent-2" />
        <span class="text-muted">Website:</span>
        <a v-if="website" :href="website" target="_blank" rel="noopener noreferrer" class="text-accent-2 hover:underline">{{ website }}</a>
        <span v-else class="text-muted">Not configured</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const email = config.public.supportEmail
const telegramId = config.public.supportTelegramId
const website = config.public.supportWebsite

useSeoMeta({ title: 'Contact Support' })
</script>
