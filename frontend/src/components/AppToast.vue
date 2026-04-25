<script setup>
import { useToast } from '@/composables/useToast'

const toast = useToast()
</script>

<template>
  <div class="toast-stack" aria-live="polite" aria-atomic="true">
    <div
      v-for="item in toast.toasts"
      :key="item.id"
      class="toast"
      :class="`is-${item.type}`"
      role="status"
    >
      <span>{{ item.message }}</span>
      <button class="toast-close" aria-label="Dismiss" @click="toast.removeToast(item.id)">x</button>
    </div>
  </div>
</template>