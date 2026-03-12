<template>
  <header class="sticky top-0 z-50 bg-surface/80 backdrop-blur-md border-b border-border">
    <div class="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
      <!-- Logo -->
      <NuxtLink to="/" class="flex items-center gap-2 font-bold text-lg tracking-tight">
        <span class="text-accent font-mono">▼</span>
        <span>Mirrorino</span>
      </NuxtLink>

      <!-- Search -->
      <div class="hidden md:flex flex-1 max-w-md">
        <div class="relative w-full">
          <Icon name="mdilocal:magnify" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted w-4 h-4" />
          <input v-model="search" @keyup.enter="doSearch" placeholder="Search repositories..." class="input pl-9 py-1.5 text-xs" />
        </div>
      </div>

      <!-- Nav -->
      <nav class="flex items-center gap-1">
        <NuxtLink to="/explore" class="btn-ghost text-sm">Explore</NuxtLink>
        <template v-if="isLoggedIn">
          <NuxtLink v-if="isAdmin" to="/admin" class="btn-ghost text-sm">Admin</NuxtLink>
          <NuxtLink :to="myReposHref" class="btn-ghost text-sm">My Repos</NuxtLink>
          <div class="relative" ref="menuRef">
            <button @click="menuOpen = !menuOpen" class="w-8 h-8 rounded-full bg-surface-2 border border-border flex items-center justify-center text-sm font-mono hover:border-accent transition-colors">
              {{ user?.username?.[0]?.toUpperCase() }}
            </button>
            <div v-if="menuOpen" class="absolute right-0 top-10 w-52 card shadow-xl py-1 z-50">
              <div class="px-3 py-2 border-b border-border">
                <p class="text-sm font-medium">{{ user?.username }}</p>
                <p class="text-xs text-muted truncate">{{ user?.email }}</p>
              </div>
              <NuxtLink :to="myReposHref" class="flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-2" @click="menuOpen=false">
                <Icon name="mdilocal:repo-clone" class="w-4 h-4" /> Repositories
              </NuxtLink>
              <NuxtLink to="/user/settings" class="flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-2" @click="menuOpen=false">
                <Icon name="mdilocal:cog-outline" class="w-4 h-4" /> Settings
              </NuxtLink>
              <div class="border-t border-border mt-1">
                <button @click="logout" class="w-full flex items-center gap-2 px-3 py-2 text-sm text-danger hover:bg-surface-2">
                  <Icon name="mdilocal:logout" class="w-4 h-4" /> Sign out
                </button>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <NuxtLink to="/login" class="btn-ghost text-sm">Sign in</NuxtLink>
          <NuxtLink to="/register" class="btn-primary text-sm py-1.5">Sign up</NuxtLink>
        </template>
      </nav>
    </div>

    <div class="md:hidden px-4 pb-3">
      <div class="relative w-full">
        <Icon name="mdilocal:magnify" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted w-4 h-4" />
        <input v-model="search" @keyup.enter="doSearch" placeholder="Search repositories..." class="input pl-9 py-1.5 text-xs" />
      </div>
    </div>

    <div class="w-full border-t border-accent-2/40 bg-accent-2/10 text-accent-2">
      <div lang="fa" dir="rtl" class="max-w-7xl mx-auto px-4 py-2 text-center text-xs sm:text-sm font-persian">
        این وبسایت صرفا به عنوان یک میرور گیت هاب برای توسعه دهندگان است و پایبند به قوانین است
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
const { user, isLoggedIn, isAdmin, logout } = useAuth()
const search = ref('')
const menuOpen = ref(false)
const menuRef = ref<HTMLElement>()

onClickOutside(menuRef, () => { menuOpen.value = false })

function doSearch() {
  if (search.value.trim()) navigateTo(`/search?q=${encodeURIComponent(search.value.trim())}`)
}

const myReposHref = computed(() => (user.value?.username ? `/${user.value.username}/repos` : '/user/repos'))
</script>
