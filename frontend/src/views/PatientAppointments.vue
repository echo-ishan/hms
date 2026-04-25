<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DepartmentIcon from '@/components/DepartmentIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { usePatientStore } from '@/stores/patient'
import { useToast } from '@/composables/useToast'

const auth = useAuthStore()
const patientStore = usePatientStore()
const toast = useToast()
const route = useRoute()
const router = useRouter()

const loadingDoctors = ref(true)
const loadingAvailability = ref(false)
const error = ref('')
const selectedDateHint = ref('')
const weeklyAvailability = ref([])
const pendingPrefillDate = ref('')
const showBookingForm = ref(false)
const showTreatmentView = ref(false)
const selectedTreatment = ref(null)

const filters = reactive({
  status: '',
})

const booking = reactive({
  department_id: '',
  doctor_id: '',
  date: '',
  start_clock: '',
  end_clock: '',
  visit_reason: '',
})

function toIsoDate(date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 10)
}

const weekDays = computed(() => {
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date()
    date.setDate(date.getDate() + index)
    const value = toIsoDate(date)
    return {
      value,
      label: date.toLocaleDateString(undefined, {
        weekday: 'short',
        day: '2-digit',
        month: 'short',
      }),
    }
  })
})

const doctorsByDepartment = computed(() => {
  if (!booking.department_id) return patientStore.doctors
  return patientStore.doctors.filter((doctor) => String(doctor.department_id || '') === String(booking.department_id))
})

const selectedDepartmentName = computed(() => {
  return patientStore.departments.find((item) => String(item.id) === String(booking.department_id))?.name || ''
})

const selectedDoctorName = computed(() => {
  return patientStore.doctors.find((item) => String(item.id) === String(booking.doctor_id))?.name || ''
})

const completedAppointments = computed(() => {
  return [...patientStore.appointments]
    .filter((item) => item.status === 'completed')
    .sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())
})

function getAppointmentDepartmentName(appointment) {
  const doctor = patientStore.doctors.find((item) => Number(item.id) === Number(appointment.doctor_id))
  return doctor?.department_name || 'Department not set'
}

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

function combineDateAndClock(date, clock) {
  return `${date}T${clock}:00`
}

function openTreatmentView(appointment) {
  selectedTreatment.value = appointment
  showTreatmentView.value = true
}

function closeTreatmentView() {
  showTreatmentView.value = false
  selectedTreatment.value = null
}

async function loadDoctorAvailability({ resetDateHint = true } = {}) {
  weeklyAvailability.value = []
  if (resetDateHint) selectedDateHint.value = ''
  if (!booking.doctor_id) return

  loadingAvailability.value = true
  try {
    const doctorId = Number(booking.doctor_id)
    const entries = await Promise.all(
      weekDays.value.map(async (day) => {
        const slots = await patientStore.fetchDoctorAvailability(doctorId, { date: day.value })
        return { ...day, slots }
      })
    )
    weeklyAvailability.value = entries
  } catch (err) {
    error.value = err.message || 'Failed to load doctor availability'
  } finally {
    loadingAvailability.value = false
  }
}

function selectAvailabilityDate(day) {
  booking.date = day.value
  selectedDateHint.value = day.label
}

function applyPrefillFromQuery() {
  const doctorId = route.query.doctor_id ? String(route.query.doctor_id) : ''
  const date = route.query.date ? String(route.query.date) : ''

  if (doctorId || date) {
    showBookingForm.value = true
  }

  if (doctorId) {
    booking.doctor_id = doctorId
    const selectedDoctor = patientStore.doctors.find((item) => String(item.id) === doctorId)
    booking.department_id = selectedDoctor?.department_id ? String(selectedDoctor.department_id) : ''
  }

  if (date) {
    pendingPrefillDate.value = date
    booking.date = date
    selectedDateHint.value = date
  }

  if (doctorId || date) {
    const nextQuery = { ...route.query }
    delete nextQuery.doctor_id
    delete nextQuery.date
    router.replace({ query: nextQuery })
  }
}

function toggleBookingForm() {
  showBookingForm.value = !showBookingForm.value
}

async function loadData() {
  error.value = ''
  loadingDoctors.value = true
  try {
    await Promise.all([
      patientStore.fetchDoctors(),
      patientStore.fetchDepartments(),
      patientStore.fetchAppointments({ status: filters.status }, auth.accessToken),
    ])
    applyPrefillFromQuery()
    await loadDoctorAvailability({ resetDateHint: !booking.date })
  } catch (err) {
    error.value = err.message || 'Failed to load appointments data'
  } finally {
    loadingDoctors.value = false
  }
}

async function submitBooking() {
  error.value = ''
  try {
    await patientStore.bookAppointment(
      {
        doctor_id: Number(booking.doctor_id),
        start_time: combineDateAndClock(booking.date, booking.start_clock),
        end_time: combineDateAndClock(booking.date, booking.end_clock),
        visit_reason: booking.visit_reason || null,
      },
      auth.accessToken
    )
    toast.showSuccess('Appointment booked successfully.')
    booking.department_id = ''
    booking.doctor_id = ''
    booking.date = ''
    booking.start_clock = ''
    booking.end_clock = ''
    booking.visit_reason = ''
    showBookingForm.value = false
    weeklyAvailability.value = []
    await loadData()
  } catch (err) {
    const message = err.message || 'Failed to book appointment'
    error.value = message
    toast.showError(message)
  }
}

async function cancelAppointment(id) {
  if (!window.confirm('Cancel this appointment?')) return
  try {
    await patientStore.cancelAppointment(id, auth.accessToken)
    toast.showSuccess('Appointment cancelled.')
    await loadData()
  } catch (err) {
    const message = err.message || 'Failed to cancel appointment'
    error.value = message
    toast.showError(message)
  }
}

watch(
  () => booking.department_id,
  (value) => {
    if (!value) return
    if (!doctorsByDepartment.value.some((doctor) => String(doctor.id) === String(booking.doctor_id))) {
      booking.doctor_id = ''
      weeklyAvailability.value = []
    }
  }
)

watch(
  () => booking.doctor_id,
  async () => {
    const hasPrefillDate = Boolean(pendingPrefillDate.value)
    booking.date = hasPrefillDate ? pendingPrefillDate.value : ''
    selectedDateHint.value = hasPrefillDate ? pendingPrefillDate.value : ''
    booking.start_clock = ''
    booking.end_clock = ''
    await loadDoctorAvailability({ resetDateHint: !hasPrefillDate })
    pendingPrefillDate.value = ''
  }
)

watch(
  () => route.query,
  async () => {
    if (!patientStore.doctors.length) return
    applyPrefillFromQuery()
    await loadDoctorAvailability({ resetDateHint: !booking.date })
  }
)

onMounted(loadData)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Appointments</h1>
        <p class="page-subtitle">Book doctor appointments and manage existing bookings.</p>
      </div>
      <button class="btn primary" type="button" @click="toggleBookingForm">
        {{ showBookingForm ? 'Hide Booking Form' : 'Book Appointment' }}
      </button>
    </div>

    <form v-if="showBookingForm" class="card form-grid" @submit.prevent="submitBooking">
      <h3 class="form-row-full">Book Appointment</h3>
      <div class="form-row">
        <label>Department</label>
        <select v-model="booking.department_id">
          <option value="">All Departments</option>
          <option v-for="department in patientStore.departments" :key="department.id" :value="department.id">
            {{ department.name }}
          </option>
        </select>
        <small v-if="selectedDepartmentName" class="muted department-meta">
          <DepartmentIcon :department-name="selectedDepartmentName" />
          <span>{{ selectedDepartmentName }}</span>
        </small>
      </div>
      <div class="form-row">
        <label>Doctor</label>
        <select v-model="booking.doctor_id" required>
          <option value="">Select doctor</option>
          <option v-for="doctor in doctorsByDepartment" :key="doctor.id" :value="doctor.id">
            {{ doctor.name }} ({{ doctor.department_name || 'No department' }})
          </option>
        </select>
        <small v-if="selectedDoctorName" class="muted">Selected: {{ selectedDoctorName }}</small>
      </div>
      <div class="form-row">
        <label>Date</label>
        <input v-model="booking.date" type="date" required />
        <small v-if="selectedDateHint" class="muted">Picked from weekly availability: {{ selectedDateHint }}</small>
      </div>
      <div class="form-row">
        <label>Start Time</label>
        <input v-model="booking.start_clock" type="time" required />
      </div>
      <div class="form-row">
        <label>End Time</label>
        <input v-model="booking.end_clock" type="time" required />
      </div>
      <div class="form-row form-row-full">
        <label>Visit Reason</label>
        <textarea v-model="booking.visit_reason" rows="2" />
      </div>
      <div class="form-row form-row-full">
        <label>Doctor Availability (Next 7 Days)</label>
        <p v-if="!booking.doctor_id" class="muted">Select a doctor to view available slots.</p>
        <p v-else-if="loadingAvailability" class="muted">Loading weekly availability...</p>
        <div v-else class="week-grid">
          <div v-for="day in weeklyAvailability" :key="day.value" class="week-cell">
            <small class="muted">{{ day.label }}</small>
            <button
              class="slot-pill"
              :class="day.slots.length > 0 ? 'is-available' : 'is-unavailable'"
              type="button"
              :disabled="day.slots.length === 0"
              @click="selectAvailabilityDate(day)"
            >
              {{ day.slots.length > 0 ? `Use Date (${day.slots.length} slot${day.slots.length === 1 ? '' : 's'})` : 'No slots' }}
            </button>
            <div v-for="slot in day.slots" :key="slot.id" class="muted">
              {{ slot.start_time }} - {{ slot.end_time }}
            </div>
          </div>
        </div>
      </div>
      <div class="button-row">
        <button class="btn primary" type="submit">Book</button>
      </div>
    </form>

    <div class="card stack-md">
      <div class="toolbar">
        <select v-model="filters.status">
          <option value="">All Status</option>
          <option value="booked">Booked</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <button class="btn" @click="loadData">Filter</button>
        <p class="muted">{{ patientStore.appointments.length }} records</p>
      </div>

      <div v-if="error" class="alert error">{{ error }}</div>
      <p v-if="patientStore.loadingAppointments || loadingDoctors">Loading appointments...</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Doctor</th>
            <th>Department</th>
            <th>Start</th>
            <th>End</th>
            <th>Status</th>
            <th>Visit Reason</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in patientStore.appointments" :key="item.id">
            <td>{{ item.doctor_name || '-' }}</td>
            <td>
              <span class="department-meta">
                <DepartmentIcon :department-name="getAppointmentDepartmentName(item)" />
                <span>{{ getAppointmentDepartmentName(item) }}</span>
              </span>
            </td>
            <td>{{ item.start_time || '-' }}</td>
            <td>{{ item.end_time || '-' }}</td>
            <td>
              <span class="badge" :class="item.status === 'completed' ? 'ok' : item.status === 'booked' ? 'warn' : 'danger'">
                {{ item.status }}
              </span>
            </td>
            <td>{{ item.visit_reason || '-' }}</td>
            <td class="actions-cell">
              <button v-if="item.status === 'booked'" class="btn small danger" @click="cancelAppointment(item.id)">
                Cancel
              </button>
              <button v-if="item.status === 'completed'" class="btn small" @click="openTreatmentView(item)">
                View Treatment
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="stack-md">
        <div class="section-header">
          <h3>Completed Treatment Records</h3>
        </div>
        <p v-if="!completedAppointments.length" class="muted">No completed treatments yet.</p>
        <div v-else class="treatment-preview-list">
          <article v-for="item in completedAppointments" :key="item.id" class="treatment-preview card">
            <div class="stack-md">
              <p><strong>{{ item.doctor_name || '-' }}</strong></p>
              <p class="muted department-meta">
                <DepartmentIcon :department-name="getAppointmentDepartmentName(item)" />
                <span>{{ getAppointmentDepartmentName(item) }}</span>
              </p>
              <p class="muted">{{ formatDateTime(item.start_time) }}</p>
              <p><strong>Diagnosis:</strong> {{ item.diagnosis || '-' }}</p>
            </div>
            <button class="btn small" type="button" @click="openTreatmentView(item)">View Treatment</button>
          </article>
        </div>
      </div>
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
            <DepartmentIcon :department-name="getAppointmentDepartmentName(selectedTreatment)" />
            <span><strong>Department:</strong> {{ getAppointmentDepartmentName(selectedTreatment) }}</span>
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
