<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold">Ads</h1>
      <button @click="showCreate=true" class="btn-primary text-sm py-1.5"><Icon name="mdi:plus" class="w-4 h-4" /> New Ad</button>
    </div>
    <div class="space-y-3">
      <div v-for="ad in ads" :key="ad.id" class="card p-4 flex items-center gap-4">
        <img :src="ad.image_url" class="w-16 h-10 object-cover rounded border border-border" />
        <div class="flex-1 min-w-0">
          <p class="font-medium text-sm">{{ ad.title }}</p>
          <p class="text-xs text-muted truncate">{{ ad.target_url }}</p>
          <p class="text-xs text-muted font-mono mt-0.5">{{ ad.position }} · {{ ad.click_count }} clicks</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button @click="toggleAd(ad)" class="text-xs font-mono px-2 py-1 rounded border" :class="ad.is_active ? 'border-success/30 text-success' : 'border-border text-muted'">
            {{ ad.is_active ? 'Active' : 'Inactive' }}
          </button>
          <button @click="deleteAd(ad.id)" class="btn-ghost py-1 px-2 text-xs text-danger"><Icon name="mdi:trash-can-outline" class="w-4 h-4" /></button>
        </div>
      </div>
    </div>

    <!-- Create Ad Modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4" @click.self="showCreate=false">
      <div class="card p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-4">New Advertisement</h2>
        <div class="space-y-3">
          <div><label class="text-xs text-muted block mb-1.5">Title</label><input v-model="form.title" class="input" /></div>
          <div><label class="text-xs text-muted block mb-1.5">Image URL</label><input v-model="form.image_url" class="input" /></div>
          <div><label class="text-xs text-muted block mb-1.5">Target URL</label><input v-model="form.target_url" class="input" /></div>
          <div>
            <label class="text-xs text-muted block mb-1.5">Position</label>
            <select v-model="form.position" class="input">
              <option value="sidebar">Sidebar</option>
              <option value="banner">Banner</option>
              <option value="inline">Inline</option>
            </select>
          </div>
          <div class="flex gap-2 pt-2">
            <button @click="showCreate=false" class="btn-secondary flex-1 justify-center">Cancel</button>
            <button @click="createAd" class="btn-primary flex-1 justify-center">Create</button>
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
const { data: ads, refresh } = await useAsyncData('admin-ads', () => get<Ad[]>('/api/admin/ads'))
const showCreate = ref(false)
const form = reactive({ title: '', image_url: '', target_url: '', position: 'sidebar', is_active: true })
async function createAd() {
  await post('/api/admin/ads', { ...form })
  showCreate.value = false
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
