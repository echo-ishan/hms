<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DepartmentIcon from '@/components/DepartmentIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { usePatientStore } from '@/stores/patient'

const router = useRouter()
const auth = useAuthStore()
const patientStore = usePatientStore()

const loading = ref(true)
const error = ref('')
const search = ref('')
const departmentFilter = ref('')
const weekAvailability = ref({})

const selectedDepartmentName = computed(() => {
  return patientStore.departments.find((item) => String(item.id) === String(departmentFilter.value))?.name || ''
})

function toIsoDate(date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 10)
}

const weekDays = computed(() => {
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date()
    date.setDate(date.getDate() + index)
    return {
      value: toIsoDate(date),
      label: date.toLocaleDateString(undefined, {
        weekday: 'short',
        day: '2-digit',
        month: 'short',
      }),
    }
  })
})

const nowTimestamp = () => new Date().getTime()

const upcomingAppointments = computed(() => {
  return patientStore.appointments
    .filter((item) => item.status === 'booked' && new Date(item.start_time).getTime() >= nowTimestamp())
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
})

const upcomingCount = computed(() => upcomingAppointments.value.length)

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  return date.toLocaleString(undefined, {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function doctorAvatarUrl(id) {
  return `https://picsum.photos/seed/doctor-${id}/56/56`
}

function getAppointmentDepartmentName(appointment) {
  const doctor = patientStore.doctors.find((item) => Number(item.id) === Number(appointment.doctor_id))
  return doctor?.department_name || 'Department not set'
}

async function loadDoctorsAndAvailability() {
  loading.value = true
  error.value = ''
  weekAvailability.value = {}

  try {
    await Promise.all([
      patientStore.fetchDepartments(),
      patientStore.fetchDoctors({ q: search.value, department_id: departmentFilter.value }),
      patientStore.fetchAppointments({}, auth.accessToken),
    ])

    const entries = await Promise.all(
      patientStore.doctors.map(async (doctor) => {
        const perDay = await Promise.all(
          weekDays.value.map(async (day) => {
            const slots = await patientStore.fetchDoctorAvailability(doctor.id, { date: day.value })
            return { date: day.value, label: day.label, count: slots.length }
          })
        )
        return [doctor.id, perDay]
      })
    )

    weekAvailability.value = Object.fromEntries(entries)
  } catch (err) {
    error.value = err.message || 'Failed to load doctors and weekly availability'
  } finally {
    loading.value = false
  }
}

function goToAppointments() {
  router.push('/patient/appointments')
}

function goToDoctorBooking(doctorId, date = '') {
  const query = { doctor_id: String(doctorId) }
  if (date) query.date = date
  router.push({ name: 'patient-appointments', query })
}

onMounted(loadDoctorsAndAvailability)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">Patient Dashboard</h1>
        <p class="page-subtitle">Browse doctor profiles and check availability for the coming 7 days.</p>
      </div>
      <button class="btn primary" @click="goToAppointments">Book / Manage Appointments</button>
    </div>

    <div class="stats-grid">
      <article class="card stat-card">
        <h3>Doctors</h3>
        <p class="stat-value">{{ patientStore.doctors.length }}</p>
      </article>
      <article class="card stat-card">
        <h3>Departments</h3>
        <p class="stat-value">{{ patientStore.departments.length }}</p>
      </article>
      <article class="card stat-card">
        <h3>Upcoming Appointments</h3>
        <p class="stat-value">{{ upcomingCount }}</p>
      </article>
      <article class="card stat-card">
        <h3>All My Appointments</h3>
        <p class="stat-value">{{ patientStore.appointments.length }}</p>
      </article>
    </div>

    <article class="card stack-md">
      <div class="section-header">
        <h3>Upcoming Appointments</h3>
        <button class="btn" @click="goToAppointments">Manage All</button>
      </div>
      <p v-if="!upcomingCount" class="muted">No upcoming appointments yet.</p>
      <ul v-else class="activity-list">
        <li v-for="appointment in upcomingAppointments" :key="appointment.id" class="activity-item">
          <p><strong>{{ appointment.doctor_name || 'Doctor' }}</strong></p>
          <p class="muted department-meta">
            <DepartmentIcon :department-name="getAppointmentDepartmentName(appointment)" />
            <span>{{ getAppointmentDepartmentName(appointment) }}</span>
          </p>
          <p class="muted">{{ formatDateTime(appointment.start_time) }} to {{ formatDateTime(appointment.end_time) }}</p>
          <p class="muted">Reason: {{ appointment.visit_reason || '-' }}</p>
        </li>
      </ul>
    </article>

    <div class="card stack-md">
      <div class="toolbar">
        <input v-model.trim="search" placeholder="Search doctors by name/email" @keyup.enter="loadDoctorsAndAvailability" />
        <select v-model="departmentFilter">
          <option value="">All Departments</option>
          <option v-for="department in patientStore.departments" :key="department.id" :value="department.id">
            {{ department.name }}
          </option>
        </select>
        <small v-if="selectedDepartmentName" class="muted department-meta">
          <DepartmentIcon :department-name="selectedDepartmentName" />
          <span>{{ selectedDepartmentName }}</span>
        </small>
        <button class="btn" @click="loadDoctorsAndAvailability">Search</button>
      </div>

      <div v-if="error" class="alert error">{{ error }}</div>
      <p v-if="loading">Loading doctors and weekly availability...</p>

      <div v-else class="stack-md">
        <article v-for="doctor in patientStore.doctors" :key="doctor.id" class="card stack-md">
          <div class="person-cell">
            <img :src="doctorAvatarUrl(doctor.id)" alt="Doctor profile" class="avatar" />
            <div>
              <p class="person-name">{{ doctor.name }}</p>
              <p class="muted">{{ doctor.email }}</p>
              <p class="muted department-meta">
                <DepartmentIcon :department-name="doctor.department_name" />
                <span>{{ doctor.department_name || 'Department not set' }}</span>
              </p>
            </div>
          </div>
          <p><strong>Experience:</strong> {{ doctor.years_experience ?? '-' }} years</p>
          <p><strong>Contact:</strong> {{ doctor.contact_number || '-' }}</p>
          <p><strong>Bio:</strong> {{ doctor.bio || '-' }}</p>
          <div class="week-grid">
            <div v-for="day in weekAvailability[doctor.id] || []" :key="day.date" class="week-cell">
              <small class="muted">{{ day.label }}</small>
              <button
                class="slot-pill"
                :class="day.count > 0 ? 'is-available' : 'is-unavailable'"
                :disabled="day.count === 0"
                @click="goToDoctorBooking(doctor.id, day.date)"
              >
                {{ day.count > 0 ? `${day.count} slot${day.count === 1 ? '' : 's'}` : 'No slots' }}
              </button>
            </div>
          </div>
          <div class="button-row">
            <button class="btn primary" @click="goToDoctorBooking(doctor.id)">Book With {{ doctor.name }}</button>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>
