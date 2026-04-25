<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AdminShell from '@/components/AdminShell.vue'
import DoctorShell from '@/components/DoctorShell.vue'
import PatientShell from '@/components/PatientShell.vue'
import AppToast from '@/components/AppToast.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const useAdminShell = computed(() => route.path.startsWith('/admin'))
const useDoctorShell = computed(() => route.path.startsWith('/doctor'))
const usePatientShell = computed(() => route.path.startsWith('/patient'))

onMounted(async () => {
  await auth.bootstrap()
})
</script>

<template>
  <AppToast />
  <AdminShell v-if="useAdminShell">
    <RouterView />
  </AdminShell>
  <DoctorShell v-else-if="useDoctorShell">
    <RouterView />
  </DoctorShell>
  <PatientShell v-else-if="usePatientShell">
    <RouterView />
  </PatientShell>
  <RouterView v-else />
</template>
