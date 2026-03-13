<template>
  <component
    :is="linkTag"
    v-if="repo.is_mirror"
    :href="isValidLink ? mirrorInfo?.normalizedUrl : undefined"
    :target="isValidLink ? '_blank' : undefined"
    :rel="isValidLink ? 'noopener noreferrer' : undefined"
    class="group block w-full rounded-xl border px-4 py-3 transition-all duration-300"
    :class="[platformMeta.boxClass, isValidLink ? 'hover:-translate-y-0.5 hover:shadow-lg' : 'opacity-95']"
  >
    <div class="flex items-start gap-3">
      <div class="w-10 h-10 rounded-lg bg-surface/70 border border-border/70 flex items-center justify-center shrink-0 overflow-hidden">
        <img :src="platformMeta.iconPath" :alt="`${platformMeta.label} icon`" class="w-5 h-5 object-contain" loading="lazy" decoding="async">
      </div>

      <div class="min-w-0 flex-1">
        <p class="text-[11px] uppercase tracking-wider text-muted font-mono mb-1">Mirror source · {{ platformMeta.label }}</p>
        <p class="text-sm font-semibold truncate">{{ displayPath }}</p>
        <p class="text-xs text-muted truncate mt-0.5">{{ displayUrl }}</p>
        <p v-if="!isValidLink" class="text-[11px] text-warning mt-1">Enter a valid http(s) source URL to enable link preview.</p>
      </div>

      <Icon
        v-if="isValidLink"
        name="mdilocal:open-in-new"
        class="w-4 h-4 text-muted group-hover:text-foreground transition-colors"
      />
    </div>
  </component>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'
import { getMirrorPlatformMeta, parseMirrorUrl } from '~/utils/mirror'

const props = defineProps<{ repo: Repo }>()

const mirrorInfo = computed(() => parseMirrorUrl(props.repo.source_url))
const platformMeta = computed(() => getMirrorPlatformMeta(mirrorInfo.value?.platform || 'other'))
const isValidLink = computed(() => !!mirrorInfo.value?.isValid)
const linkTag = computed(() => (isValidLink.value ? 'a' : 'div'))
const displayPath = computed(() => mirrorInfo.value?.displayPath || 'Source repository')
const displayUrl = computed(() => mirrorInfo.value?.normalizedUrl || props.repo.source_url || '')
</script>
