<template>
  <a
    v-if="repo.is_mirror && mirrorInfo"
    :href="mirrorInfo.normalizedUrl"
    target="_blank"
    rel="noopener noreferrer"
    class="group w-full rounded-xl border px-4 py-3 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg"
    :class="platformMeta.boxClass"
  >
    <div class="flex items-start gap-3">
      <div class="w-10 h-10 rounded-lg bg-surface/70 border border-border/70 flex items-center justify-center shrink-0">
        <Icon :name="platformMeta.icon" class="w-5 h-5" />
      </div>
      <div class="min-w-0 flex-1">
        <p class="text-[11px] uppercase tracking-wider text-muted font-mono mb-1">Mirror source · {{ platformMeta.label }}</p>
        <p class="text-sm font-semibold truncate">{{ mirrorInfo.displayPath }}</p>
        <p class="text-xs text-muted truncate mt-0.5">{{ mirrorInfo.normalizedUrl }}</p>
      </div>
      <Icon name="mdilocal:open-in-new" class="w-4 h-4 text-muted group-hover:text-foreground transition-colors" />
    </div>
  </a>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'
import { getMirrorPlatformMeta, parseMirrorUrl } from '~/utils/mirror'

const props = defineProps<{ repo: Repo }>()
const mirrorInfo = computed(() => parseMirrorUrl(props.repo.source_url))
const platformMeta = computed(() => getMirrorPlatformMeta(mirrorInfo.value?.platform || 'other'))
</script>
