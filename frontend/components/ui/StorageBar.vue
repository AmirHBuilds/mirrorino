<template>
  <div>
    <div class="flex justify-between text-xs text-muted mb-1.5">
      <span>{{ formatBytes(used) }} used</span>
      <span>{{ formatBytes(limit) }} total</span>
    </div>
    <div class="h-1.5 bg-surface-2 rounded-full overflow-hidden">
      <div class="h-full rounded-full transition-all duration-500"
        :class="pct > 90 ? 'bg-danger' : pct > 70 ? 'bg-warning' : 'bg-success'"
        :style="{ width: `${Math.min(pct, 100)}%` }" />
    </div>
    <p class="text-xs text-muted mt-1">{{ formatBytes(limit - used) }} remaining</p>
  </div>
</template>

<script setup lang="ts">
import { formatBytes } from '~/utils/format'
const props = defineProps<{ used: number; limit: number }>()
const pct = computed(() => props.limit > 0 ? (props.used / props.limit) * 100 : 0)
</script>
