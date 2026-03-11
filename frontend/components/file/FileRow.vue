<template>
  <div class="flex items-center gap-3 px-4 py-2.5 hover:bg-surface-2/50 transition-colors group">
    <Icon :name="fileIcon(file.original_name)" class="w-4 h-4 text-muted shrink-0" />
    <a :href="rawHref" target="_blank" rel="noopener noreferrer" class="text-sm font-mono flex-1 min-w-0 truncate hover:underline text-accent-2">{{ file.original_name }}</a>
    <span class="text-xs text-muted font-mono hidden sm:block">{{ formatBytes(file.size_bytes) }}</span>
    <span class="text-xs text-muted hidden md:block">{{ formatRelative(file.uploaded_at) }}</span>
    <span class="text-xs text-muted font-mono hidden lg:flex items-center gap-1">
      <Icon name="mdilocal:download-outline" class="w-3.5 h-3.5" />{{ file.download_count }}
    </span>
    <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
      <button v-if="canEdit" @click="$emit('edit', file)" class="btn-ghost py-1 px-2 text-xs" :aria-label="`Edit ${file.original_name}`" title="Edit file">
        <Icon name="mdilocal:pencil-outline" class="w-3.5 h-3.5" />
      </button>
      <a :href="downloadHref" class="btn-ghost py-1 px-2 text-xs" :aria-label="`Download ${file.original_name}`">
        <Icon name="mdilocal:download" class="w-3.5 h-3.5" />
      </a>
      <button v-if="canDelete" @click="$emit('delete', file.id)" class="btn-ghost py-1 px-2 text-xs text-danger hover:text-danger">
        <Icon name="mdilocal:trash-can-outline" class="w-3.5 h-3.5" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatBytes, formatRelative, fileIcon } from '~/utils/format'
import type { RepoFile } from '~/types'
const props = defineProps<{ file: RepoFile; repoUsername: string; repoSlug: string; canDelete?: boolean; canEdit?: boolean }>()
defineEmits<{ delete: [id: number]; edit: [file: RepoFile] }>()
const apiBase = useRuntimeConfig().public.apiBase
const fullPath = computed(() => props.file.directory_path ? `${props.file.directory_path}/${props.file.original_name}` : props.file.original_name)
const encodePathForUrl = (path: string) => path.split('/').map((segment) => encodeURIComponent(segment)).join('/')
const rawHref = computed(() => `${apiBase}/raw/${props.repoUsername}/${props.repoSlug}/${encodePathForUrl(fullPath.value)}`)
const downloadHref = computed(() => `${apiBase}/api/users/${props.repoUsername}/repos/${props.repoSlug}/files/${props.file.id}/download`)
</script>
