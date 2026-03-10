<template>
  <div>
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
      <h1 class="text-xl font-bold">Repositories</h1>
      <div class="flex flex-col sm:flex-row gap-2">
        <input v-model="filters.q" @input="debouncedRefresh" placeholder="Search name, slug, owner..." class="input py-1.5 text-sm w-full sm:w-64" />
        <select v-model="filters.verification_status" @change="refresh" class="input py-1.5 text-sm w-full sm:w-44">
          <option value="">All statuses</option>
          <option value="unverified">Unverified</option>
          <option value="pending">Pending</option>
          <option value="verified">Verified</option>
          <option value="rejected">Rejected</option>
        </select>
        <select v-model="filters.visibility" @change="refresh" class="input py-1.5 text-sm w-full sm:w-36">
          <option value="">All visibility</option>
          <option value="true">Public</option>
          <option value="false">Private</option>
        </select>
      </div>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead class="border-b border-border">
          <tr class="text-xs text-muted font-mono">
            <th class="text-left px-4 py-3">Repository</th>
            <th class="text-left px-4 py-3 hidden md:table-cell">Owner</th>
            <th class="text-left px-4 py-3 hidden lg:table-cell">Stats</th>
            <th class="text-left px-4 py-3">Status</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          <tr v-for="repo in repos" :key="repo.id" class="hover:bg-surface-2/40 transition-colors">
            <td class="px-4 py-3">
              <p class="font-medium">{{ repo.name }}</p>
              <p class="text-xs text-muted">/{{ repo.owner.username }}/{{ repo.slug }}</p>
            </td>
            <td class="px-4 py-3 hidden md:table-cell text-xs text-muted">{{ repo.owner.username }}</td>
            <td class="px-4 py-3 hidden lg:table-cell text-xs text-muted font-mono">
              {{ repo.file_count }} files · {{ formatBytes(repo.total_size) }} · {{ repo.download_count }} dl
            </td>
            <td class="px-4 py-3">
              <div class="flex flex-col gap-1">
                <span class="text-xs px-2 py-0.5 rounded-full border w-fit" :class="statusClass(repo.verification_status)">{{ repo.verification_status }}</span>
                <span class="text-[11px] text-muted">{{ repo.is_public ? 'Public' : 'Private' }}</span>
              </div>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-1 justify-end">
                <button class="btn-ghost py-1 px-2 text-xs" @click="setVisibility(repo, !repo.is_public)">{{ repo.is_public ? 'Make Private' : 'Make Public' }}</button>
                <button class="btn-ghost py-1 px-2 text-xs" @click="openStatus(repo)">Set Status</button>
                <button class="btn-ghost py-1 px-2 text-xs text-danger" @click="deleteRepo(repo.id)"><Icon name="mdilocal:trash-can-outline" class="w-3.5 h-3.5" /></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="editing" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4" @click.self="editing = null">
      <div class="card p-6 w-full max-w-lg">
        <h2 class="text-lg font-semibold mb-4">Update Repository Status</h2>
        <p class="text-sm text-muted mb-4">{{ editing.name }} by {{ editing.owner.username }}</p>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-muted block mb-1.5">Verification status</label>
            <select v-model="editForm.verification_status" class="input">
              <option value="unverified">Unverified</option>
              <option value="pending">Pending</option>
              <option value="verified">Verified</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-muted block mb-1.5">Admin note</label>
            <textarea v-model="editForm.verification_note" rows="3" class="input"></textarea>
          </div>
        </div>
        <div class="flex gap-2 pt-4">
          <button @click="editing = null" class="btn-secondary flex-1 justify-center">Cancel</button>
          <button @click="saveStatus" class="btn-primary flex-1 justify-center">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'
import { formatBytes } from '~/utils/format'
definePageMeta({ layout: 'admin', middleware: 'admin' })
useSeoMeta({ title: 'Admin · Repositories' })
const { get, put, delete: del } = useApi()

const filters = reactive({ q: '', verification_status: '', visibility: '' })

const { data: repos, refresh } = await useAsyncData(
  () => `admin-repos:${JSON.stringify(filters)}`,
  () => get<Repo[]>(`/api/admin/repos${queryString()}`),
  { server: false, default: () => [] },
)

const debouncedRefresh = useDebounceFn(() => refresh(), 400)

const editing = ref<Repo | null>(null)
const editForm = reactive({ verification_status: 'unverified', verification_note: '' })

function queryString() {
  const query = new URLSearchParams()
  if (filters.q) query.set('q', filters.q)
  if (filters.verification_status) query.set('verification_status', filters.verification_status)
  if (filters.visibility) query.set('is_public', filters.visibility)
  return query.toString() ? `?${query.toString()}` : ''
}

function statusClass(status: Repo['verification_status']) {
  if (status === 'verified') return 'border-success/30 text-success'
  if (status === 'pending') return 'border-warning/30 text-warning'
  if (status === 'rejected') return 'border-danger/30 text-danger'
  return 'border-border text-muted'
}

function openStatus(repo: Repo) {
  editing.value = repo
  editForm.verification_status = repo.verification_status
  editForm.verification_note = ''
}

async function saveStatus() {
  if (!editing.value) return
  await put(`/api/admin/repos/${editing.value.id}`, {
    verification_status: editForm.verification_status,
    verification_note: editForm.verification_note || null,
  })
  editing.value = null
  await refresh()
}

async function setVisibility(repo: Repo, next: boolean) {
  await put(`/api/admin/repos/${repo.id}`, { is_public: next })
  await refresh()
}

async function deleteRepo(id: number) {
  if (!confirm('Delete this repository and all files?')) return
  await del(`/api/admin/repos/${id}`)
  await refresh()
}
</script>
