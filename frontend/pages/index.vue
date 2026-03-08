<template>
  <div>
    <!-- Most downloaded repos (top) -->
    <section class="max-w-7xl mx-auto px-4 py-8">
      <div class="card p-6 mb-8 border-accent/20 bg-gradient-to-b from-accent/10 to-transparent">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <p class="text-xs font-mono uppercase tracking-wider text-muted">Top of Downloadino</p>
            <h2 class="text-2xl font-semibold">Most downloaded repositories</h2>
          </div>
          <NuxtLink to="/explore" class="btn-primary text-sm py-1.5">Explore all repos</NuxtLink>
        </div>
        <p class="text-sm text-muted">Discover what users download the most right now.</p>
      </div>

      <div v-if="pending" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
        <div v-for="i in 6" :key="i" class="card p-4 animate-pulse h-32"></div>
      </div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
        <RepoCard v-for="repo in repos" :key="repo.id" :repo="repo" />
      </div>
    </section>

    <!-- Hero -->
    <section class="border-y border-border py-20">
      <div class="max-w-4xl mx-auto px-4 text-center">
        <div class="inline-flex items-center gap-2 text-xs font-mono text-muted bg-surface-1 border border-border rounded-full px-3 py-1 mb-8">
          <span class="w-1.5 h-1.5 rounded-full bg-success animate-pulse"></span>
          Self-hosted · Iranian intranet ready
        </div>
        <h1 class="text-5xl sm:text-6xl font-bold tracking-tight mb-6 leading-tight">
          Host & share<br><span class="text-accent">files freely</span>
        </h1>
        <p class="text-lg text-muted max-w-xl mx-auto mb-10">
          GitHub-style file repositories for scripts, tools, and binaries. Share installation commands. Works fully offline.
        </p>
        <div class="flex items-center justify-center gap-3">
          <NuxtLink to="/register" class="btn-primary px-6 py-2.5">Get started free</NuxtLink>
          <NuxtLink to="/explore" class="btn-secondary px-6 py-2.5">Explore repos</NuxtLink>
        </div>
        <!-- install command demo -->
        <div class="mt-12 max-w-lg mx-auto">
          <div class="card overflow-hidden">
            <div class="flex items-center gap-2 px-4 py-2 bg-surface-2 border-b border-border">
              <div class="flex gap-1.5"><div class="w-2.5 h-2.5 rounded-full bg-danger/50"></div><div class="w-2.5 h-2.5 rounded-full bg-warning/50"></div><div class="w-2.5 h-2.5 rounded-full bg-success/50"></div></div>
              <span class="text-xs text-muted font-mono ml-1">terminal</span>
            </div>
            <div class="px-4 py-4 font-mono text-sm text-left">
              <span class="text-success">$</span>
              <span class="text-fg ml-2">bash &lt;(curl -Ls https://api.downloadino.com/raw/</span><span class="text-accent">username</span><span class="text-fg">/</span><span class="text-accent-2">my-tool</span><span class="text-fg">/install.sh)</span>
            </div>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import type { Repo } from '~/types'
useSeoMeta({ title: 'Home' })
const { get } = useApi()
const { data: repos, pending } = await useAsyncData(
  'home-repos',
  () => get<Repo[]>('/api/repos/?limit=6&sort=downloads'),
  { server: false, default: () => [] },
)
</script>
