<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DepartmentIcon from '@/components/DepartmentIcon.vue'
import { getPatientExportStatus, requestPatientTreatmentsExport } from '@/api/patient'
import { useAuthStore } from '@/stores/auth'
import { usePatientStore } from '@/stores/patient'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const auth = useAuthStore()
const patientStore = usePatientStore()
const toast = useToast()

const loading = ref(true)
const error = ref('')
const showTreatmentView = ref(false)
const selectedTreatment = ref(null)
const exportInProgress = ref(false)
const exportTaskId = ref('')
let exportPollTimer = null

const patientName = computed(() => {
  return patientStore.profile?.name || auth.user?.name || auth.user?.email || 'Patient'
})

const doctorById = computed(() => {
  return Object.fromEntries(patientStore.doctors.map((doctor) => [Number(doctor.id), doctor]))
})

const completedAppointments = computed(() => {
  return patientStore.appointments.filter((item) => item.status === 'completed')
})

const historyRows = computed(() => {
  const sorted = [...completedAppointments.value].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  )

  return sorted.map((item, index) => {
    const doctor = doctorById.value[Number(item.doctor_id)] || null
    return {
      ...item,
      visit_no: index + 1,
      doctor_name: item.doctor_name || doctor?.name || '-',
      department_name: doctor?.department_name || 'Department not set',
    }
  })
})

const visitedDepartments = computed(() => {
  const names = new Set(
    historyRows.value
      .map((item) => item.department_name)
      .filter((value) => value && value !== 'Department not set')
  )
  return Array.from(names)
})

const completedVisits = computed(() => historyRows.value.length)

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function openTreatmentView(row) {
  selectedTreatment.value = row
  showTreatmentView.value = true
}

function closeTreatmentView() {
  showTreatmentView.value = false
  selectedTreatment.value = null
}

function stopExportPolling() {
  if (exportPollTimer) {
    clearInterval(exportPollTimer)
    exportPollTimer = null
  }
}

async function pollExportStatus() {
  if (!exportTaskId.value) return
  try {
    const data = await getPatientExportStatus(exportTaskId.value, auth.accessToken)
    if (data.state === 'SUCCESS') {
      exportInProgress.value = false
      stopExportPolling()
      toast.showSuccess('CSV export is complete. Check your email for notification.')
      return
    }
    if (data.state === 'FAILURE') {
      exportInProgress.value = false
      stopExportPolling()
      toast.showError(data.error || 'CSV export failed.')
    }
  } catch (err) {
    exportInProgress.value = false
    stopExportPolling()
    toast.showError(err.message || 'Failed to check export status.')
  }
}

async function exportHistoryCsv() {
  if (exportInProgress.value) return
  try {
    exportInProgress.value = true
    const data = await requestPatientTreatmentsExport(auth.accessToken)
    exportTaskId.value = data.task_id || ''
    toast.showSuccess('CSV export started. You will be notified by email once done.')
    stopExportPolling()
    exportPollTimer = setInterval(pollExportStatus, 3000)
  } catch (err) {
    exportInProgress.value = false
    toast.showError(err.message || 'Failed to start CSV export.')
  }
}

async function loadHistory() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([
      patientStore.fetchProfile(auth.accessToken),
      patientStore.fetchDoctors(),
      patientStore.fetchDepartments(),
      patientStore.fetchAppointments({}, auth.accessToken),
    ])
  } catch (err) {
    error.value = err.message || 'Failed to load patient history'
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/patient/dashboard')
}

onMounted(loadHistory)
onUnmounted(stopExportPolling)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">Patient History</h1>
        <p class="page-subtitle">See your visit history, doctor details, and treatment records in one place.</p>
      </div>
      <div class="button-row">
        <button class="btn" type="button" :disabled="exportInProgress" @click="exportHistoryCsv">
          {{ exportInProgress ? 'Exporting...' : 'Export as CSV' }}
        </button>
        <button class="btn primary" type="button" @click="goBack">Back</button>
      </div>
    </div>

    <div class="card stack-md">
      <p><strong>Patient Name:</strong> {{ patientName }}</p>
      <p><strong>Total Completed Appointments:</strong> {{ historyRows.length }}</p>
      <p><strong>Completed Visits:</strong> {{ completedVisits }}</p>
      <p><strong>Departments:</strong> {{ visitedDepartments.length ? visitedDepartments.join(', ') : '-' }}</p>
    </div>

    <div v-if="error" class="alert error">{{ error }}</div>
    <p v-if="loading">Loading patient history...</p>

    <div v-else class="card stack-md">
      <h3>Completed Treatment Timeline</h3>
      <p v-if="!historyRows.length" class="muted">No completed appointments found yet.</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Visit No.</th>
            <th>Date</th>
            <th>Doctor</th>
            <th>Department</th>
            <th>Status</th>
            <th>Visit Type</th>
            <th>Tests Done</th>
            <th>Diagnosis</th>
            <th>Prescription</th>
            <th>Medicines</th>
            <th>Notes</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in historyRows" :key="row.id">
            <td>{{ row.visit_no }}</td>
            <td>{{ formatDateTime(row.start_time) }}</td>
            <td>{{ row.doctor_name }}</td>
            <td>
              <span class="department-meta">
                <DepartmentIcon :department-name="row.department_name" />
                <span>{{ row.department_name }}</span>
              </span>
            </td>
            <td>
              <span class="badge" :class="row.status === 'completed' ? 'ok' : row.status === 'booked' ? 'warn' : 'danger'">
                {{ row.status || '-' }}
              </span>
            </td>
            <td>In-person</td>
            <td>{{ row.tests_requested || '-' }}</td>
            <td>{{ row.diagnosis || '-' }}</td>
            <td>{{ row.prescription || '-' }}</td>
            <td>{{ row.medications_prescribed || '-' }}</td>
            <td>{{ row.notes || '-' }}</td>
            <td class="actions-cell">
              <button v-if="row.status === 'completed'" class="btn small" type="button" @click="openTreatmentView(row)">
                View Treatment
              </button>
              <span v-else>-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showTreatmentView && selectedTreatment" class="treatment-modal-backdrop" @click.self="closeTreatmentView">
      <article class="card treatment-modal stack-md" role="dialog" aria-modal="true" aria-label="Treatment details">
        <div class="section-header">
          <h3>Treatment Details</h3>
          <button class="btn small" type="button" @click="closeTreatmentView">Close</button>
        </div>

        <div class="treatment-grid">
          <p><strong>Doctor:</strong> {{ selectedTreatment.doctor_name || '-' }}</p>
          <p class="department-meta">
            <DepartmentIcon :department-name="selectedTreatment.department_name" />
            <span><strong>Department:</strong> {{ selectedTreatment.department_name || '-' }}</span>
          </p>
          <p><strong>Visit Date:</strong> {{ formatDateTime(selectedTreatment.start_time) }}</p>
          <p><strong>Status:</strong> {{ selectedTreatment.status || '-' }}</p>
        </div>

        <div class="treatment-grid">
          <p><strong>Visit Reason:</strong> {{ selectedTreatment.visit_reason || '-' }}</p>
          <p><strong>Tests Done:</strong> {{ selectedTreatment.tests_requested || '-' }}</p>
          <p><strong>Diagnosis:</strong> {{ selectedTreatment.diagnosis || '-' }}</p>
          <p><strong>Prescription:</strong> {{ selectedTreatment.prescription || '-' }}</p>
          <p><strong>Medicines:</strong> {{ selectedTreatment.medications_prescribed || '-' }}</p>
          <p><strong>Follow-up Date:</strong> {{ selectedTreatment.follow_up_date || '-' }}</p>
          <p><strong>Clinical Notes:</strong> {{ selectedTreatment.notes || '-' }}</p>
        </div>
      </article>
    </div>
  </section>
</template>
