<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <div class="card p-4 text-sm text-muted">Redirecting to your repositories…</div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { user, fetchUser } = useAuth()

await useAsyncData('my-repos-redirect', async () => {
  if (!user.value) await fetchUser()
  if (!user.value?.username) {
    await navigateTo('/login')
    return null
  }

  await navigateTo(`/${user.value.username}/repos`, { replace: true })
  return null
})
</script>
