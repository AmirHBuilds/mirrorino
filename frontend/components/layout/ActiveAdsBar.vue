<template>
  <section v-if="visibleAds.length" class="border-b border-border bg-surface-1/70">
    <div class="max-w-7xl mx-auto px-4 py-3" :class="containerClass">
      <a
        v-for="(ad, idx) in visibleAds"
        :key="ad.id"
        :href="ad.target_url"
        target="_blank"
        rel="noopener noreferrer"
        class="group card overflow-hidden hover:border-accent/40 transition-colors relative"
        :class="cardClass(idx)"
        @click.prevent="openAd(ad)"
      >
        <AdMedia :src="ad.image_url" :alt="ad.title" />
        <div class="p-2.5 bg-surface-1/90">
          <span class="inline-block text-[10px] uppercase tracking-wide text-muted mb-1">Sponsored</span>
          <p class="text-xs font-semibold truncate">{{ ad.title }}</p>
        </div>
      </a>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Ad } from '~/types'

const { ads, trackClick } = useAds()

const visibleAds = computed(() => ads.value.filter((ad) => ad.position === 'banner').slice(0, 3))

const containerClass = computed(() => {
  const count = visibleAds.value.length
  if (count === 1) return 'flex justify-center'
  if (count === 2) return 'grid gap-3 sm:grid-cols-2'
  return 'grid gap-3 sm:grid-cols-2 lg:grid-cols-3'
})

function cardClass(idx: number) {
  const count = visibleAds.value.length
  if (count === 1) return 'w-full max-w-xl'
  if (count === 2) return idx === 0 ? 'justify-self-start w-full' : 'justify-self-end w-full'
  return 'w-full'
}

async function openAd(ad: Ad) {
  await trackClick(ad.id)
  window.open(ad.target_url, '_blank', 'noopener')
}
</script>
