<template>
  <div>
    <div @dragover.prevent @drop.prevent="onDrop" @click="inputRef?.click()"
      class="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-accent-2 transition-colors"
      :class="isDragging ? 'border-accent-2 bg-accent-2/5' : ''"
      @dragenter="isDragging=true" @dragleave="isDragging=false">
      <Icon name="mdilocal:cloud-upload-outline" class="w-10 h-10 text-muted mx-auto mb-3" />
      <p class="text-sm text-fg mb-1">Drop files here or <span class="text-accent-2">browse</span></p>
      <button type="button" @click.stop="inputRef?.click()" class="btn-secondary text-xs mt-3">Select files</button>
      <p class="text-xs text-muted">Max 500MB per file · Some unsafe binaries are blocked</p>
      <input ref="inputRef" type="file" multiple class="hidden" @change="onSelect" />
    </div>

    <!-- Upload queue -->
    <div v-if="queue.length" class="mt-3 space-y-2">
      <TransitionGroup name="upload-log" tag="div" class="space-y-2">
      <div v-for="item in queue" :key="item.id" class="card px-3 py-2">
        <div class="flex items-center justify-between mb-1.5 gap-2">
          <span class="text-xs font-mono truncate max-w-xs">{{ item.name }}</span>
          <div class="flex items-center gap-2">
            <span class="text-xs font-mono" :class="item.status === 'error' ? 'text-danger' : item.status === 'done' ? 'text-success' : item.status === 'queued' ? 'text-muted' : 'text-muted'">
              {{ item.status === 'error' ? item.error : item.status === 'done' ? '✓ Done' : item.status === 'queued' ? 'Queued' : `${item.progress}%` }}
            </span>
            <button
              type="button"
              class="text-muted hover:text-danger transition-colors"
              :disabled="item.status === 'uploading'"
              @click="removeFromQueue(item.id)"
              :title="item.status === 'uploading' ? 'Cannot remove while uploading' : 'Remove from queue'"
            >
              <Icon name="mdilocal:trash-can-outline" class="w-4 h-4" />
            </button>
          </div>
        </div>
        <div class="h-1 bg-surface-2 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all"
            :class="item.status === 'error' ? 'bg-danger' : item.status === 'done' ? 'bg-success' : item.status === 'queued' ? 'bg-surface-3' : 'bg-accent-2'"
            :style="{ width: `${item.status === 'queued' ? 0 : item.progress}%` }" />
        </div>
      </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ repoUsername: string; repoSlug: string; directoryPath?: string }>()
const emit  = defineEmits<{ uploaded: [] }>()

const { uploadFile } = useApi()
const isDragging = ref(false)
const inputRef   = ref<HTMLInputElement>()
const processing = ref(false)

interface QueueItem {
  id: string
  file: File
  name: string
  progress: number
  status: 'queued' | 'uploading' | 'done' | 'error'
  error?: string
  doneTimeout?: ReturnType<typeof setTimeout>
}
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

function removeFromQueue(id: string) {
  const item = queue.value.find((entry) => entry.id === id)
  if (!item || item.status === 'uploading') return
  if (item.doneTimeout) clearTimeout(item.doneTimeout)
  queue.value = queue.value.filter((entry) => entry.id !== id)
}

function uploadAll(files: File[]) {
  if (!files.length) return
  for (const file of files) {
    const item = reactive<QueueItem>({
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      file,
      name: file.name,
      progress: 0,
      status: 'queued',
    })
    queue.value.push(item)
  }
  processQueue()
}

async function processQueue() {
  if (processing.value) return
  processing.value = true

  try {
    while (true) {
      const item = queue.value.find((entry) => entry.status === 'queued')
      if (!item) break

      item.status = 'uploading'
      const fd = new FormData()
      fd.append('file', item.file)
      fd.append('directory_path', props.directoryPath || '')

      try {
        await uploadFile(`/api/users/${props.repoUsername}/repos/${props.repoSlug}/files`, fd, (pct) => { item.progress = pct })
        item.status = 'done'
        item.progress = 100
        item.doneTimeout = setTimeout(() => {
          queue.value = queue.value.filter((entry) => entry.id !== item.id)
        }, 10000)
        emit('uploaded')
      } catch (err: any) {
        item.status = 'error'
        item.error = err.message
      }
    }
  } finally {
    processing.value = false
  }
}
</script>


<style scoped>
.upload-log-enter-active,
.upload-log-leave-active {
  transition: all 0.35s ease;
}

.upload-log-enter-from,
.upload-log-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
