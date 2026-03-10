<template>
  <video
    v-if="isVideo"
    :src="src"
    class="w-full h-full object-cover"
    autoplay
    loop
    muted
    playsinline
  />
  <img v-else :src="src" :alt="alt" class="w-full h-full object-cover" loading="lazy" />
</template>

<script setup lang="ts">
const props = defineProps<{ src: string; alt: string }>()

const isVideo = computed(() => /\.(mp4|webm|ogg)(\?.*)?$/i.test(props.src))
</script>
