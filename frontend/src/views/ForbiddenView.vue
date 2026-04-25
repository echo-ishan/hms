<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const message = computed(() => {
  if (route.query.reason === 'doctor_only') {
    return 'This area is available only for authenticated doctor users.'
  }
  if (route.query.reason === 'patient_only') {
    return 'This area is available only for authenticated patient users.'
  }
  return 'This area is available only for authenticated admin users.'
})
</script>

<template>
  <section class="centered-page card stack-md">
    <h2>Access Restricted</h2>
    <p class="muted">{{ message }}</p>
    <RouterLink to="/" class="btn">Go Home</RouterLink>
  </section>
</template>
