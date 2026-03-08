<template>
  <div>
    <div @dragover.prevent @drop.prevent="onDrop" @click="inputRef?.click()"
      class="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-accent-2 transition-colors"
      :class="isDragging ? 'border-accent-2 bg-accent-2/5' : ''"
      @dragenter="isDragging=true" @dragleave="isDragging=false">
      <Icon name="mdi:cloud-upload-outline" class="w-10 h-10 text-muted mx-auto mb-3" />
      <p class="text-sm text-fg mb-1">Drop files here or <span class="text-accent-2">browse</span></p>
      <button type="button" @click.stop="inputRef?.click()" class="btn-secondary text-xs mt-3">Select files</button>
      <p class="text-xs text-muted">Max 500MB per file · Executables blocked</p>
      <input ref="inputRef" type="file" multiple class="hidden" @change="onSelect" />
    </div>

    <!-- Upload queue -->
    <div v-if="queue.length" class="mt-3 space-y-2">
      <div v-for="item in queue" :key="item.name" class="card px-3 py-2">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-xs font-mono truncate max-w-xs">{{ item.name }}</span>
          <span class="text-xs font-mono" :class="item.status === 'error' ? 'text-danger' : item.status === 'done' ? 'text-success' : 'text-muted'">
            {{ item.status === 'error' ? item.error : item.status === 'done' ? '✓ Done' : `${item.progress}%` }}
          </span>
        </div>
        <div class="h-1 bg-surface-2 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all"
            :class="item.status === 'error' ? 'bg-danger' : item.status === 'done' ? 'bg-success' : 'bg-accent-2'"
            :style="{ width: `${item.progress}%` }" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ repoId: number }>()
const emit  = defineEmits<{ uploaded: [] }>()

const { uploadFile } = useApi()
const isDragging = ref(false)
const inputRef   = ref<HTMLInputElement>()

interface QueueItem { name: string; progress: number; status: 'uploading' | 'done' | 'error'; error?: string }
const queue = ref<QueueItem[]>([])

function onDrop(e: DragEvent) {
  isDragging.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  uploadAll(files)
}

function onSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  uploadAll(files)
  input.value = ""
}

async function uploadAll(files: File[]) {
  for (const file of files) {
    const item: QueueItem = { name: file.name, progress: 0, status: 'uploading' }
    queue.value.push(item)
    const fd = new FormData()
    fd.append('file', file)
    try {
      await uploadFile(`/api/repos/${props.repoId}/files`, fd, (pct) => { item.progress = pct })
      item.status = 'done'
      item.progress = 100
      emit('uploaded')
    } catch (err: any) {
      item.status = 'error'
      item.error = err.message
    }
  }
}
</script>
