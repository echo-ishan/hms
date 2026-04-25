<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getAdminStats, listAdminAppointments } from '@/api/admin'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const counts = ref({ users: 0, doctors: 0, patients: 0, departments: 0 })
const bookedAppointments = ref([])

async function loadStats() {
  loading.value = true
  error.value = ''
  try {
    const [statsData, appointmentsData] = await Promise.all([
      getAdminStats(auth.accessToken),
      listAdminAppointments({ status: 'booked', limit: 12 }, auth.accessToken),
    ])
    counts.value = statsData.counts
    bookedAppointments.value = appointmentsData.appointments || []
  } catch (err) {
    error.value = err.message || 'Failed to load stats'
  } finally {
    loading.value = false
  }
}

function goToDoctors() {
  router.push('/admin/doctors')
}

function goToDoctorRegistration() {
  router.push({ path: '/admin/doctors', query: { intent: 'create' } })
}

onMounted(loadStats)
</script>

<template>
  <section class="stack-lg">
    <div v-if="error" class="alert error">{{ error }}</div>

    <div class="page-header">
      <div>
        <h1 class="page-title">Hospital Overview</h1>
        <p class="page-subtitle">Real-time operational metrics for admin operations.</p>
      </div>
      <button class="btn primary" @click="goToDoctorRegistration">Register Doctor</button>
    </div>

    <div v-if="loading" class="card">Loading dashboard...</div>

    <div v-else class="stats-grid">
      <article class="card stat-card">
        <h3>Users</h3>
        <p class="stat-value">{{ counts.users }}</p>
      </article>
      <article class="card stat-card">
        <h3>Doctors</h3>
        <p class="stat-value">{{ counts.doctors }}</p>
      </article>
      <article class="card stat-card">
        <h3>Patients</h3>
        <p class="stat-value">{{ counts.patients }}</p>
      </article>
      <article class="card stat-card">
        <h3>Departments</h3>
        <p class="stat-value">{{ counts.departments }}</p>
      </article>
    </div>

    <article v-if="!loading" class="card stack-md">
      <div class="section-header">
        <h3>Booked Appointments</h3>
        <button class="btn small" @click="goToDoctors">View Doctors</button>
      </div>

      <div v-if="bookedAppointments.length === 0" class="muted">No booked appointments found.</div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Patient</th>
            <th>Doctor</th>
            <th>Start</th>
            <th>End</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in bookedAppointments" :key="item.id">
            <td>{{ index + 1 }}</td>
            <td>{{ item.patient_name || '-' }}</td>
            <td>{{ item.doctor_name || '-' }}</td>
            <td>{{ item.start_time ? new Date(item.start_time).toLocaleString() : '-' }}</td>
            <td>{{ item.end_time ? new Date(item.end_time).toLocaleString() : '-' }}</td>
            <td>
              <span class="badge ok">{{ item.status }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>
