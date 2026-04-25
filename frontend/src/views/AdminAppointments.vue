<script setup>
import { computed, onMounted, ref } from 'vue'
import { cancelAdminAppointment, listAdminAppointments } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const auth = useAuthStore()
const toast = useToast()

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const appointments = ref([])
const search = ref('')
const status = ref('')
const showTreatmentModal = ref(false)
const selectedAppointment = ref(null)

const statusOptions = [
  { label: 'All Statuses', value: '' },
  { label: 'Booked', value: 'booked' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' },
]

const resultsCount = computed(() => appointments.value.length)

function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function statusBadgeClass(value) {
  if (value === 'completed') return 'ok'
  if (value === 'cancelled') return 'danger'
  return 'warn'
}

function openTreatmentDetails(appointment) {
  selectedAppointment.value = appointment
  showTreatmentModal.value = true
}

function closeTreatmentDetails() {
  showTreatmentModal.value = false
  selectedAppointment.value = null
}

async function loadAppointments() {
  loading.value = true
  error.value = ''
  try {
    const data = await listAdminAppointments(
      {
        status: status.value,
        q: search.value,
      },
      auth.accessToken,
    )
    appointments.value = data.appointments || []
  } catch (err) {
    error.value = err.message || 'Failed to load appointments'
  } finally {
    loading.value = false
  }
}

async function cancelAppointment(appointmentId) {
  if (!window.confirm('Cancel this booked appointment?')) return
  saving.value = true
  error.value = ''
  try {
    await cancelAdminAppointment(appointmentId, auth.accessToken)
    toast.showSuccess('Appointment cancelled successfully.')
    await loadAppointments()
  } catch (err) {
    error.value = err.message || 'Failed to cancel appointment'
    toast.showError(error.value)
  } finally {
    saving.value = false
  }
}

onMounted(loadAppointments)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">Appointments Management</h1>
        <p class="page-subtitle">View all appointments, review completed treatment details, and cancel booked visits.</p>
      </div>
    </div>

    <div class="card stack-md">
      <div class="toolbar">
        <input v-model.trim="search" placeholder="Search by patient/doctor name or email" @keyup.enter="loadAppointments" />
        <select v-model="status">
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
        <button class="btn" @click="loadAppointments" :disabled="loading || saving">Search</button>
        <p class="muted">{{ resultsCount }} records</p>
      </div>

      <div v-if="error" class="alert error">{{ error }}</div>
      <p v-if="loading">Loading appointments...</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Patient</th>
            <th>Doctor</th>
            <th>Start</th>
            <th>End</th>
            <th>Visit Reason</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="appointment in appointments" :key="appointment.id">
            <td>#{{ appointment.id }}</td>
            <td>{{ appointment.patient_name || '-' }}</td>
            <td>{{ appointment.doctor_name || '-' }}</td>
            <td>{{ formatDateTime(appointment.start_time) }}</td>
            <td>{{ formatDateTime(appointment.end_time) }}</td>
            <td>{{ appointment.visit_reason || '-' }}</td>
            <td>
              <span class="badge" :class="statusBadgeClass(appointment.status)">{{ appointment.status }}</span>
            </td>
            <td class="actions-cell">
              <button
                v-if="appointment.status === 'completed'"
                class="btn small"
                @click="openTreatmentDetails(appointment)"
              >
                View Treatment
              </button>
              <button
                v-if="appointment.status === 'booked'"
                class="btn small danger"
                :disabled="saving"
                @click="cancelAppointment(appointment.id)"
              >
                Cancel
              </button>
              <span v-if="appointment.status !== 'completed' && appointment.status !== 'booked'" class="muted">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showTreatmentModal" class="treatment-modal-backdrop" @click.self="closeTreatmentDetails">
      <article class="card treatment-modal stack-md" role="dialog" aria-modal="true" aria-label="Treatment details">
        <div class="section-header">
          <h3>Treatment Details</h3>
          <button class="btn" @click="closeTreatmentDetails">Close</button>
        </div>

        <div class="treatment-grid">
          <div class="info-item">
            <p class="info-label">Appointment ID</p>
            <p class="info-value">#{{ selectedAppointment?.id || '-' }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Patient</p>
            <p class="info-value">{{ selectedAppointment?.patient_name || '-' }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Doctor</p>
            <p class="info-value">{{ selectedAppointment?.doctor_name || '-' }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Completed At</p>
            <p class="info-value">{{ formatDateTime(selectedAppointment?.start_time) }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Diagnosis</p>
            <p class="info-value">{{ selectedAppointment?.diagnosis || '-' }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Prescription</p>
            <p class="info-value">{{ selectedAppointment?.prescription || '-' }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Tests Requested</p>
            <p class="info-value">{{ selectedAppointment?.tests_requested || '-' }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Medications</p>
            <p class="info-value">{{ selectedAppointment?.medications_prescribed || '-' }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Follow-up Date</p>
            <p class="info-value">{{ selectedAppointment?.follow_up_date || '-' }}</p>
          </div>
          <div class="info-item">
            <p class="info-label">Notes</p>
            <p class="info-value">{{ selectedAppointment?.notes || '-' }}</p>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
