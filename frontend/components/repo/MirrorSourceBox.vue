<template>
  <component
    :is="linkTag"
    v-if="repo.is_mirror"
    :href="isValidLink ? mirrorInfo?.normalizedUrl : undefined"
    :target="isValidLink ? '_blank' : undefined"
    :rel="isValidLink ? 'noopener noreferrer' : undefined"
    class="group block w-full rounded-lg border px-3 py-2 transition-all duration-200"
    :class="[platformMeta.boxClass, isValidLink ? 'hover:border-surface-3' : 'opacity-95']"
  >
    <div class="flex items-center gap-2.5 min-w-0">
      <span class="w-7 h-7 rounded-md bg-surface/70 border border-border/70 flex items-center justify-center shrink-0">
        <Icon :name="platformMeta.icon" class="w-4 h-4 text-accent-2 shrink-0" />
      </span>

      <div class="min-w-0 flex-1 leading-tight">
        <p class="text-[10px] uppercase tracking-wider text-muted font-mono">{{ platformMeta.label }} mirror</p>
        <p class="text-sm font-medium truncate">{{ displayPath }}</p>
      </div>

      <Icon
        v-if="isValidLink"
        name="mdilocal:web"
        class="w-3.5 h-3.5 text-muted group-hover:text-foreground transition-colors shrink-0"
      />
    </div>
    <p v-if="showUrlLine" class="mt-1 pl-9 text-[11px] text-muted truncate">{{ displayUrl }}</p>
  </component>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'
import { getMirrorPlatformMeta, parseMirrorUrl } from '~/utils/mirror'

const props = defineProps<{ repo: Repo; compact?: boolean }>()

const mirrorInfo = computed(() => parseMirrorUrl(props.repo.source_url))
const platformMeta = computed(() => getMirrorPlatformMeta(mirrorInfo.value?.platform || 'other'))
const isValidLink = computed(() => !!mirrorInfo.value?.isValid)
const linkTag = computed(() => (isValidLink.value ? 'a' : 'div'))
const displayPath = computed(() => mirrorInfo.value?.displayPath || 'Source repository')
const displayUrl = computed(() => mirrorInfo.value?.normalizedUrl || props.repo.source_url || '')
const showUrlLine = computed(() => !props.compact && !!displayUrl.value)
</script>
