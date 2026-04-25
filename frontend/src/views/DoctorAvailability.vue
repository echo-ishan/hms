<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useDoctorStore } from '@/stores/doctor'
import { useToast } from '@/composables/useToast'

const auth = useAuthStore()
const doctorStore = useDoctorStore()
const toast = useToast()

const error = ref('')
const filterDate = ref('')
const saving = ref(false)
const showCreateForm = ref(false)

function toIsoDate(date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 10)
}

const todayIso = toIsoDate(new Date())
const maxDateIso = toIsoDate(new Date(Date.now() + 6 * 24 * 60 * 60 * 1000))
const next7Days = computed(() => {
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

const form = reactive({
  date: '',
  start_time: '',
  end_time: '',
})

function pickDate(value) {
  form.date = value
}

async function loadAvailability() {
  error.value = ''
  try {
    await doctorStore.fetchAvailability({ date: filterDate.value }, auth.accessToken)
  } catch (err) {
    error.value = err.message || 'Failed to load availability'
  }
}

async function submitAvailability() {
  saving.value = true
  error.value = ''
  try {
    await doctorStore.addAvailability(
      {
        date: form.date,
        start_time: form.start_time,
        end_time: form.end_time,
      },
      auth.accessToken
    )
    toast.showSuccess('Availability slot created.')
    form.date = ''
    form.start_time = ''
    form.end_time = ''
    showCreateForm.value = false
    await loadAvailability()
  } catch (err) {
    const message = err.message || 'Failed to create availability'
    error.value = message
    toast.showError(message)
  } finally {
    saving.value = false
  }
}

function toggleCreateForm() {
  showCreateForm.value = !showCreateForm.value
}

async function removeSlot(id) {
  if (!window.confirm('Delete this availability slot?')) return
  try {
    await doctorStore.removeAvailability(id, auth.accessToken)
    toast.showSuccess('Availability slot deleted.')
    await loadAvailability()
  } catch (err) {
    const message = err.message || 'Failed to delete slot'
    error.value = message
    toast.showError(message)
  }
}

onMounted(loadAvailability)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Availability</h1>
        <p class="page-subtitle">Manage appointment slots patients can book against your schedule.</p>
      </div>
      <button class="btn primary" type="button" @click="toggleCreateForm">
        {{ showCreateForm ? 'Hide Add Slot' : 'Add Availability Slot' }}
      </button>
    </div>

    <form v-if="showCreateForm" class="card form-grid" @submit.prevent="submitAvailability">
      <h3 class="form-row-full">Add Availability Slot</h3>
      <div class="form-row form-row-full">
        <label>Quick pick (next 7 days)</label>
        <div class="chip-row">
          <button
            v-for="day in next7Days"
            :key="day.value"
            type="button"
            class="btn small"
            :class="{ primary: form.date === day.value }"
            @click="pickDate(day.value)"
          >
            {{ day.label }}
          </button>
        </div>
      </div>
      <div class="form-row">
        <label>Date</label>
        <input v-model="form.date" type="date" :min="todayIso" :max="maxDateIso" required />
        <small class="muted">Allowed range: {{ todayIso }} to {{ maxDateIso }}</small>
      </div>
      <div class="form-row">
        <label>Start Time</label>
        <input v-model="form.start_time" type="time" required />
      </div>
      <div class="form-row">
        <label>End Time</label>
        <input v-model="form.end_time" type="time" required />
      </div>
      <div class="button-row">
        <button class="btn primary" :disabled="saving">{{ saving ? 'Saving...' : 'Create Slot' }}</button>
      </div>
    </form>

    <div class="card stack-md">
      <div class="toolbar">
        <input v-model="filterDate" type="date" :min="todayIso" :max="maxDateIso" />
        <button class="btn" @click="loadAvailability">Filter</button>
        <p class="muted">{{ doctorStore.availability.length }} slots</p>
      </div>

      <div v-if="error" class="alert error">{{ error }}</div>
      <p v-if="doctorStore.loadingAvailability">Loading availability...</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Start Time</th>
            <th>End Time</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="slot in doctorStore.availability" :key="slot.id">
            <td>{{ slot.date }}</td>
            <td>{{ slot.start_time }}</td>
            <td>{{ slot.end_time }}</td>
            <td class="actions-cell">
              <button class="btn small danger" @click="removeSlot(slot.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
