<template>
  <div class="flex items-center gap-3 px-4 py-2.5 hover:bg-surface-2/50 transition-colors group">
    <Icon :name="fileIcon(file.original_name)" class="w-4 h-4 text-muted shrink-0" />
    <span class="text-sm font-mono flex-1 min-w-0 truncate">{{ file.original_name }}</span>
    <span class="text-xs text-muted font-mono hidden sm:block">{{ formatBytes(file.size_bytes) }}</span>
    <span class="text-xs text-muted hidden md:block">{{ formatRelative(file.uploaded_at) }}</span>
    <span class="text-xs text-muted font-mono hidden lg:flex items-center gap-1">
      <Icon name="mdi:download-outline" class="w-3.5 h-3.5" />{{ file.download_count }}
    </span>
    <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
      <a :href="`${apiBase}/api/files/${file.id}/download`" class="btn-ghost py-1 px-2 text-xs">
        <Icon name="mdi:download" class="w-3.5 h-3.5" />
      </a>
      <button v-if="canDelete" @click="$emit('delete', file.id)" class="btn-ghost py-1 px-2 text-xs text-danger hover:text-danger">
        <Icon name="mdi:trash-can-outline" class="w-3.5 h-3.5" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatBytes, formatRelative, fileIcon } from '~/utils/format'
import type { RepoFile } from '~/types'
defineProps<{ file: RepoFile; canDelete?: boolean }>()
defineEmits<{ delete: [id: number] }>()
const apiBase = useRuntimeConfig().public.apiBase
</script>
