<template>
  <section v-if="ads.length" class="border-b border-border bg-surface-1/70">
    <div class="max-w-7xl mx-auto px-4 py-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <a
        v-for="ad in ads.slice(0, 3)"
        :key="ad.id"
        :href="ad.target_url"
        target="_blank"
        rel="noopener noreferrer"
        class="group card overflow-hidden hover:border-accent/40 transition-colors"
        @click.prevent="openAd(ad)"
      >
        <img :src="ad.image_url" :alt="ad.title" class="w-full h-24 object-cover" />
        <div class="p-2.5">
          <p class="text-xs font-semibold truncate">{{ ad.title }}</p>
        </div>
      </a>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Ad } from '~/types'

const { get, post } = useApi()

const { data } = await useAsyncData(
  'active-ads-bar',
  () => get<Ad[]>('/api/ads/active'),
  { server: false, default: () => [] },
)

const ads = computed(() => data.value || [])

async function openAd(ad: Ad) {
  try {
    await post<{ target_url: string }>(`/api/ads/${ad.id}/click`, {})
  } catch {
    // ignore tracking issues and still open ad
  }
  window.open(ad.target_url, '_blank', 'noopener')
}
</script>
