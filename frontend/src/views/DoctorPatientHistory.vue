<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDoctorStore } from '@/stores/doctor'
import { getDoctorPatientHistory } from '@/api/doctor'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const doctorStore = useDoctorStore()

const loading = ref(true)
const error = ref('')
const historyPayload = ref(null)
const doctorScope = ref('all')

const patientId = computed(() => {
  const raw = route.query.patient_id
  if (Array.isArray(raw)) return raw[0] || ''
  return raw || ''
})

const patientName = computed(() => {
  const raw = route.query.patient_name
  if (Array.isArray(raw)) return raw[0] || ''
  return raw || ''
})

const doctorName = computed(() => {
  return doctorStore.profile?.name || auth.user?.name || auth.user?.email || 'Doctor'
})

const currentDoctorId = computed(() => Number(doctorStore.profile?.id || auth.user?.id || 0))

const treatingDoctors = computed(() => {
  const names = new Set(
    treatmentRows.value.map((item) => item.doctor_name).filter((value) => Boolean(value && value !== '-'))
  )
  return Array.from(names)
})

const patientMeta = computed(() => {
  return historyPayload.value?.patient || null
})

const treatmentRows = computed(() => {
  const source = historyPayload.value?.appointments || []
  const filtered = source
    .filter((item) => item.status === 'completed')
    .sort((a, b) => Date.parse(a.start_time) - Date.parse(b.start_time))

  return filtered.map((item, index) => ({
    ...item,
    visitNo: index + 1,
  }))
})

const visibleRows = computed(() => {
  if (doctorScope.value !== 'mine') return treatmentRows.value
  const targetId = currentDoctorId.value
  if (!targetId) return treatmentRows.value

  return treatmentRows.value
    .filter((item) => Number(item.doctor_id || 0) === targetId)
    .map((item, index) => ({
      ...item,
      visitNo: index + 1,
    }))
})

function formatDateTime(value) {
  if (!value) return '-'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString()
}

async function loadData() {
  if (!patientId.value) {
    error.value = 'Patient selection is missing.'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''

  try {
    const [, historyData] = await Promise.all([
      doctorStore.fetchProfile(auth.accessToken),
      getDoctorPatientHistory(patientId.value, auth.accessToken),
    ])
    historyPayload.value = historyData
  } catch (err) {
    error.value = err.message || 'Failed to load patient treatment history'
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/doctor/dashboard')
}

onMounted(loadData)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">Patient History</h1>
      </div>
      <button class="btn" type="button" @click="goBack">Back</button>
    </div>

    <div class="card stack-sm">
      <p><strong>Patient Name:</strong> {{ patientMeta?.name || patientName || '-' }}</p>
      <p><strong>Requested By:</strong> {{ doctorName }}</p>
      <p><strong>Treating Doctors:</strong> {{ treatingDoctors.length ? treatingDoctors.join(', ') : '-' }}</p>
      <div class="toolbar">
        <label for="doctor-scope">View:</label>
        <select id="doctor-scope" v-model="doctorScope">
          <option value="all">All Doctors</option>
          <option value="mine">Only Me</option>
        </select>
      </div>
    </div>

    <div v-if="error" class="alert error">{{ error }}</div>
    <p v-if="loading">Loading patient history...</p>

    <div v-else class="card stack-md">
      <p v-if="!visibleRows.length" class="muted">No completed treatment records found for this filter.</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Visit No.</th>
            <th>Date</th>
            <th>Doctor</th>
            <th>Department</th>
            <th>Visit Type</th>
            <th>Tests Done</th>
            <th>Diagnosis</th>
            <th>Prescription</th>
            <th>Medicines</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in visibleRows" :key="row.id">
            <td>{{ row.visitNo }}.</td>
            <td>{{ formatDateTime(row.start_time) }}</td>
            <td>{{ row.doctor_name || '-' }}</td>
            <td>{{ row.department_name || '-' }}</td>
            <td>In-person</td>
            <td>{{ row.tests_requested || '-' }}</td>
            <td>{{ row.diagnosis || '-' }}</td>
            <td>{{ row.prescription || '-' }}</td>
            <td>{{ row.medications_prescribed || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
