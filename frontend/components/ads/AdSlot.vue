<template>
  <section v-if="items.length" :class="wrapperClass">
    <div :class="containerClass">
      <a
        v-for="ad in items"
        :key="ad.id"
        :href="ad.target_url"
        target="_blank"
        rel="noopener noreferrer"
        class="card overflow-hidden transition-all hover:border-accent/40"
        @click.prevent="openAd(ad)"
      >
        <div :class="mediaClass">
          <AdMedia :src="ad.image_url" :alt="ad.title" />
        </div>
        <div class="p-3">
          <p class="text-[10px] uppercase tracking-wider text-muted mb-1">Sponsored</p>
          <p class="text-sm font-semibold line-clamp-1">{{ ad.title }}</p>
          <p v-if="ad.description" class="text-xs text-muted line-clamp-2 mt-1">{{ ad.description }}</p>
        </div>
      </a>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Ad } from '~/types'

const props = withDefaults(
  defineProps<{
    position: string
    limit?: number
    compact?: boolean
    wrapperClass?: string
  }>(),
  {
    limit: 3,
    compact: false,
    wrapperClass: '',
  },
)

const { ads, trackClick } = useAds()

const items = computed(() => ads.value.filter((ad) => ad.position === props.position).slice(0, props.limit))
const containerClass = computed(() =>
  props.compact
    ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3'
    : 'grid grid-cols-1 md:grid-cols-2 gap-4',
)
const mediaClass = computed(() => (props.compact ? 'h-24' : 'h-40'))

async function openAd(ad: Ad) {
  await trackClick(ad.id)
  window.open(ad.target_url, '_blank', 'noopener')
}
</script>
