<script setup>
import { computed, onMounted, ref } from 'vue'
import { createPatient, deletePatient, listPatients, updatePatient } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const auth = useAuthStore()
const toast = useToast()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const patients = ref([])
const search = ref('')
const editingId = ref(null)
const showForm = ref(false)

const genderOptions = ['Male', 'Female', 'Other']

const form = ref({
  name: '',
  email: '',
  password: '',
  dob: '',
  contact_number: '',
  gender: '',
  blood_group: '',
  past_medical_history: '',
  emergency_contact: '',
  address: '',
  is_active: true,
})

const submitLabel = computed(() => (editingId.value ? 'Update Patient' : 'Add Patient'))

function avatarUrl(id) {
  return `https://picsum.photos/seed/patient-${id}/56/56`
}

function resetForm() {
  editingId.value = null
  showForm.value = false
  form.value = {
    name: '',
    email: '',
    password: '',
    dob: '',
    contact_number: '',
    gender: '',
    blood_group: '',
    past_medical_history: '',
    emergency_contact: '',
    address: '',
    is_active: true,
  }
}

async function loadPatients() {
  loading.value = true
  error.value = ''
  try {
    const data = await listPatients({ q: search.value }, auth.accessToken)
    patients.value = data.patients
  } catch (err) {
    error.value = err.message || 'Failed to load patients'
  } finally {
    loading.value = false
  }
}

function startEdit(patient) {
  editingId.value = patient.id
  showForm.value = true
  form.value = {
    name: patient.name || '',
    email: patient.email || '',
    password: '',
    dob: patient.dob || '',
    contact_number: patient.contact_number || '',
    gender: patient.gender || '',
    blood_group: patient.blood_group || '',
    past_medical_history: patient.past_medical_history || '',
    emergency_contact: patient.emergency_contact || '',
    address: patient.address || '',
    is_active: Boolean(patient.is_active),
  }
}

async function submitForm() {
  saving.value = true
  error.value = ''
  try {
    const isEditing = Boolean(editingId.value)
    const payload = {
      name: form.value.name,
      email: form.value.email,
      dob: form.value.dob,
      contact_number: form.value.contact_number,
      gender: form.value.gender || null,
      blood_group: form.value.blood_group || null,
      past_medical_history: form.value.past_medical_history || null,
      emergency_contact: form.value.emergency_contact || null,
      address: form.value.address || null,
      is_active: Boolean(form.value.is_active),
    }

    if (isEditing) {
      if (form.value.password) payload.password = form.value.password
      await updatePatient(editingId.value, payload, auth.accessToken)
    } else {
      payload.password = form.value.password
      await createPatient(payload, auth.accessToken)
    }

    toast.showSuccess(isEditing ? 'Patient profile updated.' : 'Patient profile created.')
    resetForm()
    await loadPatients()
  } catch (err) {
    error.value = err.message || 'Failed to save patient'
    toast.showError(error.value)
  } finally {
    saving.value = false
  }
}

function openCreateForm() {
  showForm.value = true
  editingId.value = null
}

async function removePatient(id) {
  if (!window.confirm('Delete this patient?')) return
  try {
    await deletePatient(id, auth.accessToken)
    toast.showSuccess('Patient deleted.')
    await loadPatients()
  } catch (err) {
    error.value = err.message || 'Failed to delete patient'
    toast.showError(error.value)
  }
}

onMounted(loadPatients)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">Patients Management</h1>
        <p class="page-subtitle">Register, update, and maintain patient records and profile details.</p>
      </div>
      <button class="btn primary" @click="openCreateForm">Register Patient</button>
    </div>

    <form v-if="showForm" class="card form-grid" @submit.prevent="submitForm">
      <h3>{{ submitLabel }}</h3>
      <div class="form-row">
        <label>Name</label>
        <input v-model.trim="form.name" required />
      </div>
      <div class="form-row">
        <label>Email</label>
        <input v-model.trim="form.email" type="email" required :disabled="Boolean(editingId)" />
      </div>
      <div class="form-row">
        <label>{{ editingId ? 'New Password (optional)' : 'Password' }}</label>
        <input v-model="form.password" type="password" :required="!editingId" />
      </div>
      <div class="form-row">
        <label>Date of Birth</label>
        <input v-model="form.dob" type="date" required />
      </div>
      <div class="form-row">
        <label>Contact Number</label>
        <input v-model.trim="form.contact_number" required />
      </div>
      <div class="form-row">
        <label>Gender</label>
        <select v-model="form.gender">
          <option value="">Select gender</option>
          <option v-for="option in genderOptions" :key="option" :value="option">{{ option }}</option>
        </select>
      </div>
      <div class="form-row">
        <label>Blood Group</label>
        <input v-model.trim="form.blood_group" />
      </div>
      <div class="form-row">
        <label>Emergency Contact</label>
        <input v-model.trim="form.emergency_contact" />
      </div>
      <div class="form-row form-row-full">
        <label>Past Medical History</label>
        <textarea v-model="form.past_medical_history" rows="3" />
      </div>
      <div class="form-row form-row-full">
        <label>Address</label>
        <textarea v-model="form.address" rows="2" />
      </div>
      <div class="form-row checkbox-row">
        <label>
          <input v-model="form.is_active" type="checkbox" /> Active
        </label>
      </div>
      <div class="button-row">
        <button class="btn primary" :disabled="saving">{{ saving ? 'Saving...' : submitLabel }}</button>
        <button class="btn" type="button" @click="resetForm">Clear</button>
      </div>
    </form>

    <div class="card stack-md">
      <div class="toolbar">
        <input v-model.trim="search" placeholder="Search patient by name/email" @keyup.enter="loadPatients" />
        <button class="btn" @click="loadPatients">Search</button>
        <p class="muted">{{ patients.length }} records</p>
      </div>

      <div v-if="error" class="alert error">{{ error }}</div>
      <p v-if="loading">Loading patients...</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>Gender</th>
            <th>DOB</th>
            <th>Contact</th>
            <th>Blood Group</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="patient in patients" :key="patient.id">
            <td>
              <div class="person-cell">
                <img :src="avatarUrl(patient.id)" alt="Patient profile" class="avatar" />
                <div>
                  <p class="person-name">{{ patient.name }}</p>
                  <p class="muted">{{ patient.email }}</p>
                </div>
              </div>
            </td>
            <td>{{ patient.gender || '-' }}</td>
            <td>{{ patient.dob || '-' }}</td>
            <td>{{ patient.contact_number }}</td>
            <td>{{ patient.blood_group || '-' }}</td>
            <td><span class="badge" :class="patient.is_active ? 'ok' : 'warn'">{{ patient.is_active ? 'Active' : 'Inactive' }}</span></td>
            <td class="actions-cell">
              <button class="btn small" @click="startEdit(patient)">Edit</button>
              <button class="btn small danger" @click="removePatient(patient.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
