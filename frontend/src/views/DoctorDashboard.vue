<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDoctorStore } from '@/stores/doctor'

const router = useRouter()
const auth = useAuthStore()
const doctorStore = useDoctorStore()
const error = ref('')
const showPastMedicalHistory = ref(false)
const selectedPatientRecord = ref(null)

const upcomingCount = computed(
  () => doctorStore.appointments.filter((item) => item.status === 'booked').length
)
const completedCount = computed(
  () => doctorStore.appointments.filter((item) => item.status === 'completed').length
)
const availabilityCount = computed(() => doctorStore.availability.length)
const upcomingAppointments = computed(() => {
  const now = Date.now()
  return doctorStore.appointments
    .filter((item) => item.status === 'booked' && item.start_time)
    .filter((item) => {
      const ts = Date.parse(item.start_time)
      return Number.isFinite(ts) && ts >= now
    })
    .sort((a, b) => Date.parse(a.start_time) - Date.parse(b.start_time))
    .slice(0, 8)
})
const nextAppointmentByPatient = computed(() => {
  const now = Date.now()
  const map = new Map()

  doctorStore.appointments.forEach((item) => {
    if (!item.patient_id || item.status !== 'booked' || !item.start_time) return
    const ts = Date.parse(item.start_time)
    if (!Number.isFinite(ts) || ts < now) return
    const existing = map.get(item.patient_id)
    if (!existing || Date.parse(existing.start_time) > ts) {
      map.set(item.patient_id, item)
    }
  })

  return map
})
const lastCompletedByPatient = computed(() => {
  const map = new Map()

  doctorStore.appointments.forEach((item) => {
    if (!item.patient_id || item.status !== 'completed' || !item.start_time) return
    const ts = Date.parse(item.start_time)
    if (!Number.isFinite(ts)) return
    const existing = map.get(item.patient_id)
    if (!existing || Date.parse(existing.start_time) < ts) {
      map.set(item.patient_id, item)
    }
  })

  return map
})
const assignedPatients = computed(() => {
  const map = new Map()
  doctorStore.appointments.forEach((item) => {
    if (item.status !== 'booked') return

    const key = item.patient_id
    if (!key) return

    if (!map.has(key)) {
      map.set(key, {
        patientId: key,
        patientName: item.patient_name || `Patient #${key}`,
        patientDob: item.patient_dob || null,
        patientGender: item.patient_gender || null,
        patientBloodGroup: item.patient_blood_group || null,
        patientContactNumber: item.patient_contact_number || null,
        patientEmergencyContact: item.patient_emergency_contact || null,
        patientAddress: item.patient_address || null,
        patientPastMedicalHistory: item.patient_past_medical_history || null,
        totalAppointments: 0,
        pendingAppointments: 0,
        cancelledAppointments: 0,
        completedAppointments: 0,
        nextAppointment: null,
        lastCompletedAppointment: null,
      })
    }

    const row = map.get(key)
    row.totalAppointments += 1
    if (item.status === 'booked') {
      row.pendingAppointments += 1
    }
    if (item.status === 'cancelled') {
      row.cancelledAppointments += 1
    }
    if (item.status === 'completed') {
      row.completedAppointments += 1
    }

    if (!row.patientDob && item.patient_dob) row.patientDob = item.patient_dob
    if (!row.patientGender && item.patient_gender) row.patientGender = item.patient_gender
    if (!row.patientBloodGroup && item.patient_blood_group) row.patientBloodGroup = item.patient_blood_group
    if (!row.patientContactNumber && item.patient_contact_number) row.patientContactNumber = item.patient_contact_number
    if (!row.patientEmergencyContact && item.patient_emergency_contact) {
      row.patientEmergencyContact = item.patient_emergency_contact
    }
    if (!row.patientAddress && item.patient_address) row.patientAddress = item.patient_address
    if (!row.patientPastMedicalHistory && item.patient_past_medical_history) {
      row.patientPastMedicalHistory = item.patient_past_medical_history
    }
  })

  map.forEach((row) => {
    row.nextAppointment = nextAppointmentByPatient.value.get(row.patientId) || null
    row.lastCompletedAppointment = lastCompletedByPatient.value.get(row.patientId) || null
  })

  return Array.from(map.values()).sort((a, b) => a.patientName.localeCompare(b.patientName))
})

async function loadOverview() {
  error.value = ''
  try {
    await Promise.all([
      doctorStore.fetchProfile(auth.accessToken),
      doctorStore.fetchAppointments({}, auth.accessToken),
      doctorStore.fetchAvailability({}, auth.accessToken),
    ])
  } catch (err) {
    error.value = err.message || 'Failed to load doctor overview'
  }
}

function goToAppointments() {
  router.push('/doctor/appointments')
}

function goToAvailability() {
  router.push('/doctor/availability')
}

function formatDateTime(value) {
  if (!value) return '-'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString()
}

function formatShortDate(value) {
  if (!value) return '-'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString(undefined, {
    month: 'short',
    day: '2-digit',
    year: 'numeric',
  })
}

function ageFromDob(value) {
  if (!value) return '-'
  const dob = new Date(value)
  if (Number.isNaN(dob.getTime())) return '-'

  const today = new Date()
  let age = today.getFullYear() - dob.getFullYear()
  const monthDelta = today.getMonth() - dob.getMonth()
  if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < dob.getDate())) {
    age -= 1
  }
  return age >= 0 ? `${age} yrs` : '-'
}

function relativeWhen(value) {
  if (!value) return '-'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return '-'

  const diffMs = parsed.getTime() - Date.now()
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Today'
  if (diffDays > 0) return `In ${diffDays} day${diffDays === 1 ? '' : 's'}`
  const abs = Math.abs(diffDays)
  return `${abs} day${abs === 1 ? '' : 's'} ago`
}

function openPatientTreatmentHistory(patient) {
  router.push({
    path: '/doctor/patient-history',
    query: {
      patient_id: String(patient.patientId),
      patient_name: patient.patientName,
    },
  })
}

function openUpcomingAppointmentUpdate(item) {
  router.push({
    path: '/doctor/appointments',
    query: {
      status: 'booked',
      appointment_id: String(item.id),
      patient_id: String(item.patient_id || ''),
      patient_name: item.patient_name || '',
    },
  })
}

function openNextUpcomingAppointmentUpdate() {
  if (!upcomingAppointments.value.length) return
  openUpcomingAppointmentUpdate(upcomingAppointments.value[0])
}

function openPastMedicalHistory(patient) {
  selectedPatientRecord.value = patient
  showPastMedicalHistory.value = true
}

function closePastMedicalHistory() {
  showPastMedicalHistory.value = false
  selectedPatientRecord.value = null
}

onMounted(loadOverview)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">Doctor Dashboard</h1>
        <p class="page-subtitle">Track your appointments, schedule, and patient treatment progress.</p>
      </div>
      <button class="btn primary" @click="goToAvailability">Provide Availability</button>
    </div>

    <div v-if="error" class="alert error">{{ error }}</div>

    <div class="stats-grid">
      <article class="card stat-card">
        <h3>Upcoming Appointments</h3>
        <p class="stat-value">{{ upcomingCount }}</p>
      </article>
      <article class="card stat-card">
        <h3>Completed Appointments</h3>
        <p class="stat-value">{{ completedCount }}</p>
      </article>
      <article class="card stat-card">
        <h3>Availability Slots</h3>
        <p class="stat-value">{{ availabilityCount }}</p>
      </article>
      <article class="card stat-card">
        <h3>Assigned Patients</h3>
        <p class="stat-value">{{ assignedPatients.length }}</p>
      </article>
    </div>

    <div class="dashboard-columns">
      <article class="card stack-md">
        <div class="section-header">
          <div class="chip-row">
            <h3>Upcoming Appointments</h3>
            <button class="btn small" type="button" @click="goToAppointments">View All</button>
          </div>
        </div>
        <p v-if="!upcomingAppointments.length" class="muted">No upcoming appointments right now.</p>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Patient</th>
              <th>Start Time</th>
              <th>End Time</th>
              <th>When</th>
              <th>Visit Reason</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in upcomingAppointments" :key="item.id">
              <td>{{ index + 1 }}</td>
              <td>{{ item.patient_name || `Patient #${item.patient_id}` }}</td>
              <td>{{ formatDateTime(item.start_time) }}</td>
              <td>{{ item.end_time ? formatDateTime(item.end_time) : '-' }}</td>
              <td>{{ relativeWhen(item.start_time) }}</td>
              <td>{{ item.visit_reason || 'General consultation' }}</td>
              <td>
                <span class="badge warn">Booked</span>
              </td>
              <td class="actions-cell">
                <button class="btn small" type="button" @click="openUpcomingAppointmentUpdate(item)">
                  Update
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </article>

      <article class="card stack-md">
        <div class="section-header">
          <h3>Assigned Patients</h3>
        </div>
        <p v-if="!assignedPatients.length" class="muted">No assigned patients found yet.</p>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Patient</th>
              <th>Age / Gender</th>
              <th>Blood Group</th>
              <th>Contact</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(patient, index) in assignedPatients" :key="patient.patientId">
              <td>{{ index + 1 }}</td>
              <td>{{ patient.patientName }}</td>
              <td>{{ ageFromDob(patient.patientDob) }} / {{ patient.patientGender || '-' }}</td>
              <td>{{ patient.patientBloodGroup || '-' }}</td>
              <td>{{ patient.patientContactNumber || '-' }}</td>
              <td class="actions-cell">
                <button class="btn small" type="button" @click="openPatientTreatmentHistory(patient)">
                  Treatment
                </button>
                <button class="btn small" type="button" @click="openPastMedicalHistory(patient)">
                  PMH
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </article>
    </div>

    <div v-if="showPastMedicalHistory && selectedPatientRecord" class="treatment-modal-backdrop" @click.self="closePastMedicalHistory">
      <article class="card treatment-modal stack-md" role="dialog" aria-modal="true" aria-label="Past medical history">
        <div class="section-header">
          <h3>Past Medical History</h3>
          <button class="btn small" type="button" @click="closePastMedicalHistory">Close</button>
        </div>

        <div class="treatment-grid">
          <p><strong>Patient:</strong> {{ selectedPatientRecord.patientName }}</p>
          <p><strong>Age:</strong> {{ ageFromDob(selectedPatientRecord.patientDob) }}</p>
          <p><strong>Gender:</strong> {{ selectedPatientRecord.patientGender || '-' }}</p>
          <p><strong>Blood Group:</strong> {{ selectedPatientRecord.patientBloodGroup || '-' }}</p>
          <p><strong>Contact Number:</strong> {{ selectedPatientRecord.patientContactNumber || '-' }}</p>
          <p><strong>Emergency Contact:</strong> {{ selectedPatientRecord.patientEmergencyContact || '-' }}</p>
          <p><strong>Address:</strong> {{ selectedPatientRecord.patientAddress || '-' }}</p>
          <p>
            <strong>Completed Appointments:</strong>
            {{ selectedPatientRecord.completedAppointments }}
          </p>
        </div>

        <div class="card stack-sm">
          <h4>History Notes</h4>
          <p>
            {{ selectedPatientRecord.patientPastMedicalHistory || 'No past medical history available for this patient.' }}
          </p>
        </div>
      </article>
    </div>
  </section>
</template>
