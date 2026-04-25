<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDoctorStore } from '@/stores/doctor'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const auth = useAuthStore()
const doctorStore = useDoctorStore()
const toast = useToast()

const loading = computed(() => doctorStore.loadingAppointments)
const error = ref('')
const selectedAppointment = ref(null)
const patientIdFilter = ref('')
const patientNameFilter = ref('')
const appointmentIdFilter = ref('')

const filters = reactive({
  status: '',
  from: '',
  to: '',
})

const filteredAppointments = computed(() => {
  return doctorStore.appointments.filter((item) => {
    if (patientIdFilter.value && String(item.patient_id || '') !== String(patientIdFilter.value)) {
      return false
    }
    if (appointmentIdFilter.value && String(item.id || '') !== String(appointmentIdFilter.value)) {
      return false
    }
    return true
  })
})

const editForm = reactive({
  status: '',
  diagnosis: '',
  prescription: '',
  tests_requested: '',
  medications_prescribed: '',
  notes: '',
  follow_up_date: '',
})

function badgeClass(status) {
  if (status === 'completed') return 'ok'
  if (status === 'booked') return 'warn'
  return 'danger'
}

function statusLabel(status) {
  if (!status) return '-'
  return status[0].toUpperCase() + status.slice(1)
}

function firstQueryValue(value) {
  if (Array.isArray(value)) return value[0] || ''
  return value || ''
}

function applyRouteFilters() {
  const statusQuery = firstQueryValue(route.query.status)
  const fromQuery = firstQueryValue(route.query.from)
  const toQuery = firstQueryValue(route.query.to)
  const patientIdQuery = firstQueryValue(route.query.patient_id)
  const patientNameQuery = firstQueryValue(route.query.patient_name)
  const appointmentIdQuery = firstQueryValue(route.query.appointment_id)

  filters.status = statusQuery
  filters.from = fromQuery
  filters.to = toQuery
  patientIdFilter.value = patientIdQuery
  patientNameFilter.value = patientNameQuery
  appointmentIdFilter.value = appointmentIdQuery
}

function clearPatientFilter() {
  patientIdFilter.value = ''
  patientNameFilter.value = ''
  appointmentIdFilter.value = ''
}

function autoOpenAppointmentFromQuery() {
  if (!appointmentIdFilter.value) return
  const target = filteredAppointments.value.find(
    (item) => String(item.id || '') === String(appointmentIdFilter.value)
  )
  if (target) {
    startUpdate(target)
  }
}

async function loadAppointments() {
  error.value = ''
  try {
    await doctorStore.fetchAppointments(
      {
        status: filters.status,
        from: filters.from,
        to: filters.to,
      },
      auth.accessToken
    )
  } catch (err) {
    error.value = err.message || 'Failed to load appointments'
  }
}

function startUpdate(item) {
  selectedAppointment.value = item
  editForm.status = item.status || ''
  editForm.diagnosis = item.diagnosis || ''
  editForm.prescription = item.prescription || ''
  editForm.tests_requested = item.tests_requested || ''
  editForm.medications_prescribed = item.medications_prescribed || ''
  editForm.notes = item.notes || ''
  editForm.follow_up_date = item.follow_up_date || ''
}

function clearUpdateForm() {
  selectedAppointment.value = null
  editForm.status = ''
  editForm.diagnosis = ''
  editForm.prescription = ''
  editForm.tests_requested = ''
  editForm.medications_prescribed = ''
  editForm.notes = ''
  editForm.follow_up_date = ''
}

async function submitUpdate() {
  if (!selectedAppointment.value) return

  try {
    await doctorStore.saveAppointment(
      selectedAppointment.value.id,
      {
        status: editForm.status,
        diagnosis: editForm.diagnosis || null,
        prescription: editForm.prescription || null,
        tests_requested: editForm.tests_requested || null,
        medications_prescribed: editForm.medications_prescribed || null,
        notes: editForm.notes || null,
        follow_up_date: editForm.follow_up_date || null,
      },
      auth.accessToken
    )
    toast.showSuccess('Appointment updated successfully.')
    await loadAppointments()
    clearUpdateForm()
  } catch (err) {
    toast.showError(err.message || 'Failed to update appointment')
  }
}

watch(
  () => route.query,
  async () => {
    applyRouteFilters()
    await loadAppointments()
    autoOpenAppointmentFromQuery()
  },
  { immediate: true }
)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Appointments</h1>
        <p class="page-subtitle">Review assigned patients and update visit/treatment details.</p>
      </div>
    </div>

    <div class="card stack-md">
      <div class="toolbar">
        <select v-model="filters.status">
          <option value="">All Status</option>
          <option value="booked">Booked</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <input v-model="filters.from" type="datetime-local" />
        <input v-model="filters.to" type="datetime-local" />
        <button class="btn" @click="loadAppointments">Apply Filters</button>
        <button v-if="patientIdFilter" class="btn" type="button" @click="clearPatientFilter">
          Clear Patient Filter
        </button>
        <p class="muted">{{ filteredAppointments.length }} records</p>
      </div>

      <div v-if="patientIdFilter" class="alert">
        Showing treatment history for
        <strong>{{ patientNameFilter || `Patient #${patientIdFilter}` }}</strong>
      </div>
      <div v-if="appointmentIdFilter" class="alert">
        Focused on appointment
        <strong>#{{ appointmentIdFilter }}</strong>
      </div>

      <div v-if="error" class="alert error">{{ error }}</div>
      <p v-if="loading">Loading appointments...</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>Start Time</th>
            <th>Status</th>
            <th>Visit Context</th>
            <th>Treatment Context</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredAppointments" :key="item.id">
            <td>
              <p class="person-name">{{ item.patient_name || '-' }}</p>
            </td>
            <td>{{ item.start_time || '-' }}</td>
            <td>
              <span class="badge" :class="badgeClass(item.status)">
                {{ statusLabel(item.status) }}
              </span>
            </td>
            <td>{{ item.visit_reason || '-' }}</td>
            <td>{{ item.diagnosis || item.prescription || item.notes || '-' }}</td>
            <td class="actions-cell">
              <button class="btn small" @click="startUpdate(item)">Update</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <form v-if="selectedAppointment" class="card form-grid" @submit.prevent="submitUpdate">
      <h3 class="form-row-full">Update Appointment #{{ selectedAppointment.id }}</h3>
      <div class="form-row">
        <label>Status</label>
        <select v-model="editForm.status" required>
          <option value="booked">Booked</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
      <div class="form-row">
        <label>Follow-up Date</label>
        <input v-model="editForm.follow_up_date" type="date" />
      </div>
      <div class="form-row form-row-full">
        <label>Diagnosis</label>
        <textarea v-model="editForm.diagnosis" rows="2" />
      </div>
      <div class="form-row form-row-full">
        <label>Prescription</label>
        <textarea v-model="editForm.prescription" rows="2" />
      </div>
      <div class="form-row form-row-full">
        <label>Tests Requested</label>
        <textarea v-model="editForm.tests_requested" rows="2" />
      </div>
      <div class="form-row form-row-full">
        <label>Medications Prescribed</label>
        <textarea v-model="editForm.medications_prescribed" rows="2" />
      </div>
      <div class="form-row form-row-full">
        <label>Notes</label>
        <textarea v-model="editForm.notes" rows="2" />
      </div>
      <div class="button-row">
        <button class="btn primary" type="submit">Save Update</button>
        <button class="btn" type="button" @click="clearUpdateForm">Cancel</button>
      </div>
    </form>
  </section>
</template>
