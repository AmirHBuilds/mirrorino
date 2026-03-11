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
        <div class="h-24 sm:h-28 lg:h-32 bg-surface-2">
          <AdMedia :src="ad.image_url" :alt="ad.title" />
        </div>
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

function adPositions(position: string) {
  return position
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function pickRandomAds(list: Ad[], limit: number) {
  const shuffled = [...list]
  for (let i = shuffled.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled.slice(0, limit)
}

const visibleAds = ref<Ad[]>([])

watch(
  ads,
  () => {
    const bannerAds = ads.value.filter((ad) => adPositions(ad.position).includes('banner'))
    visibleAds.value = pickRandomAds(bannerAds, 3)
  },
  { immediate: true },
)

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
