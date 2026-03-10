<template>
  <div>
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
      <div>
        <h1 class="text-xl font-bold">Ads manager</h1>
        <p class="text-sm text-muted mt-1">Create placements for banner, homepage, explore and repository pages. GIF and video links are supported.</p>
      </div>
      <button @click="openCreate" class="btn-primary text-sm py-1.5">
        <Icon name="mdilocal:plus" class="w-4 h-4" /> New Ad
      </button>
    </div>

    <div class="card p-4 mb-4 grid grid-cols-1 md:grid-cols-3 gap-3">
      <input v-model="query" class="input" placeholder="Search title or URL" />
      <select v-model="statusFilter" class="input">
        <option value="all">All status</option>
        <option value="active">Active only</option>
        <option value="inactive">Inactive only</option>
      </select>
      <select v-model="positionFilter" class="input">
        <option value="all">All placements</option>
        <option v-for="option in placementOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
      </select>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-3">
      <div v-for="ad in filteredAds" :key="ad.id" class="card p-4 flex items-start gap-4">
        <div class="w-32 h-20 rounded border border-border overflow-hidden shrink-0 bg-surface-2">
          <AdMedia :src="ad.image_url" :alt="ad.title" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-medium text-sm">{{ ad.title }}</p>
          <p class="text-xs text-muted truncate">{{ ad.target_url }}</p>
          <p class="text-xs text-muted font-mono mt-0.5">{{ ad.position }} · {{ ad.click_count }} clicks</p>
          <p v-if="ad.description" class="text-xs text-muted mt-2 line-clamp-2">{{ ad.description }}</p>
        </div>
        <div class="flex flex-col items-end gap-2 shrink-0">
          <button @click="toggleAd(ad)" class="text-xs font-mono px-2 py-1 rounded border" :class="ad.is_active ? 'border-success/30 text-success' : 'border-border text-muted'">{{ ad.is_active ? 'Active' : 'Inactive' }}</button>
          <div class="flex items-center gap-2">
            <button @click="openEdit(ad)" class="btn-ghost py-1 px-2 text-xs">Edit</button>
            <button @click="deleteAd(ad.id)" class="btn-ghost py-1 px-2 text-xs text-danger"><Icon name="mdilocal:trash-can-outline" class="w-4 h-4" /></button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4" @click.self="showModal = false">
      <div class="card p-6 w-full max-w-lg">
        <h2 class="text-lg font-semibold mb-4">{{ editingId ? 'Edit Advertisement' : 'New Advertisement' }}</h2>
        <div class="space-y-3">
          <div><label class="text-xs text-muted block mb-1.5">Title</label><input v-model="form.title" class="input" /></div>
          <div><label class="text-xs text-muted block mb-1.5">Media URL (image / GIF / mp4)</label><input v-model="form.image_url" class="input" /></div>
          <div><label class="text-xs text-muted block mb-1.5">Target URL</label><input v-model="form.target_url" class="input" /></div>
          <div><label class="text-xs text-muted block mb-1.5">Description</label><textarea v-model="form.description" rows="3" class="input" /></div>
          <div>
            <label class="text-xs text-muted block mb-1.5">Placement</label>
            <select v-model="form.position" class="input">
              <option v-for="option in placementOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </div>
          <label class="text-xs text-muted flex items-center gap-2"><input type="checkbox" v-model="form.is_active" /> Active</label>

          <div v-if="form.image_url" class="border border-border rounded p-2 bg-surface-2">
            <p class="text-xs text-muted mb-2">Preview</p>
            <div class="h-32 rounded overflow-hidden bg-surface-1">
              <AdMedia :src="form.image_url" :alt="form.title || 'Ad preview'" />
            </div>
          </div>

          <div class="flex gap-2 pt-2">
            <button @click="showModal = false" class="btn-secondary flex-1 justify-center">Cancel</button>
            <button @click="saveAd" class="btn-primary flex-1 justify-center">{{ editingId ? 'Save' : 'Create' }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Ad } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin' })
useSeoMeta({ title: 'Admin · Ads' })

const { get, post, put, delete: del } = useApi()
const { data: ads, refresh } = await useAsyncData('admin-ads', () => get<Ad[]>('/api/admin/ads'), { server: false, default: () => [] })

const placementOptions = [
  { value: 'banner', label: 'Top banner' },
  { value: 'home_featured', label: 'Homepage featured block' },
  { value: 'home_inline', label: 'Homepage inline grid' },
  { value: 'explore_inline', label: 'Explore page inline grid' },
  { value: 'repo_inline', label: 'Repository page inline block' },
  { value: 'sidebar', label: 'Legacy sidebar' },
  { value: 'inline', label: 'Legacy inline' },
]

const query = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')
const positionFilter = ref('all')

const showModal = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ title: '', image_url: '', target_url: '', description: '', position: 'banner', is_active: true })

const filteredAds = computed(() => {
  const list = ads.value || []
  return list.filter((ad) => {
    if (statusFilter.value === 'active' && !ad.is_active) return false
    if (statusFilter.value === 'inactive' && ad.is_active) return false
    if (positionFilter.value !== 'all' && ad.position !== positionFilter.value) return false
    if (!query.value.trim()) return true

    const keyword = query.value.toLowerCase()
    return ad.title.toLowerCase().includes(keyword) || ad.target_url.toLowerCase().includes(keyword)
  })
})

function resetForm() {
  form.title = ''
  form.image_url = ''
  form.target_url = ''
  form.description = ''
  form.position = 'banner'
  form.is_active = true
}

function openCreate() {
  editingId.value = null
  resetForm()
  showModal.value = true
}

function openEdit(ad: Ad) {
  editingId.value = ad.id
  form.title = ad.title
  form.image_url = ad.image_url
  form.target_url = ad.target_url
  form.description = ad.description || ''
  form.position = ad.position
  form.is_active = ad.is_active
  showModal.value = true
}

async function saveAd() {
  const payload = { ...form, description: form.description || null }
  if (editingId.value) await put(`/api/admin/ads/${editingId.value}`, payload)
  else await post('/api/admin/ads', payload)
  showModal.value = false
  await refresh()
}

async function toggleAd(ad: Ad) {
  await put(`/api/admin/ads/${ad.id}`, { is_active: !ad.is_active })
  await refresh()
}

async function deleteAd(id: number) {
  if (!confirm('Delete this ad?')) return
  await del(`/api/admin/ads/${id}`)
  await refresh()
}
</script>
