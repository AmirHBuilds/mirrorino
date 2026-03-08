<template>
  <span :class="badgeClass">
    <Icon :name="icon" class="w-3 h-3" />
    {{ label }}
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{ status: string }>()
const config: Record<string, { class: string; icon: string; label: string }> = {
  verified:   { class: 'badge-verified',   icon: 'mdi:check-decagram', label: 'Verified' },
  pending:    { class: 'badge-pending',    icon: 'mdi:clock-outline',  label: 'Pending' },
  unverified: { class: 'badge-unverified', icon: 'mdi:alert-outline',  label: 'Unverified' },
  rejected:   { class: 'badge-rejected',   icon: 'mdi:alert-circle',   label: 'Spam' },
}
const badgeClass = computed(() => config[props.status]?.class || 'badge-unverified')
const icon       = computed(() => config[props.status]?.icon || 'mdi:alert-outline')
const label      = computed(() => config[props.status]?.label || 'Unknown')
</script>
