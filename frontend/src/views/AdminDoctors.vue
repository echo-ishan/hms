<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createDoctor, deleteDoctor, listDepartments, listDoctors, updateDoctor } from '@/api/admin'
import DepartmentIcon from '@/components/DepartmentIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const auth = useAuthStore()
const toast = useToast()
const route = useRoute()
const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const doctors = ref([])
const departments = ref([])
const search = ref('')
const departmentFilter = ref('')
const editingId = ref(null)
const showForm = ref(false)

const form = ref({
  name: '',
  email: '',
  password: '',
  department_id: '',
  license_number: '',
  contact_number: '',
  years_experience: '',
  bio: '',
  is_active: true,
})

const submitLabel = computed(() => (editingId.value ? 'Update Doctor' : 'Add Doctor'))

function avatarUrl(id) {
  return `https://picsum.photos/seed/doctor-${id}/56/56`
}

function resetForm() {
  editingId.value = null
  showForm.value = false
  form.value = {
    name: '',
    email: '',
    password: '',
    department_id: '',
    license_number: '',
    contact_number: '',
    years_experience: '',
    bio: '',
    is_active: true,
  }
}

async function loadDoctors() {
  loading.value = true
  error.value = ''
  try {
    const [doctorData, departmentData] = await Promise.all([
      listDoctors({ q: search.value, department_id: departmentFilter.value }, auth.accessToken),
      listDepartments(auth.accessToken),
    ])
    doctors.value = doctorData.doctors
    departments.value = departmentData.departments
  } catch (err) {
    error.value = err.message || 'Failed to load doctors'
  } finally {
    loading.value = false
  }
}

function startEdit(doctor) {
  editingId.value = doctor.id
  showForm.value = true
  form.value = {
    name: doctor.name || '',
    email: doctor.email || '',
    password: '',
    department_id: doctor.department_id || '',
    license_number: doctor.license_number || '',
    contact_number: doctor.contact_number || '',
    years_experience: doctor.years_experience ?? '',
    bio: doctor.bio || '',
    is_active: Boolean(doctor.is_active),
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
      department_id: form.value.department_id || null,
      license_number: form.value.license_number || null,
      contact_number: form.value.contact_number || null,
      years_experience: form.value.years_experience === '' ? null : Number(form.value.years_experience),
      bio: form.value.bio || null,
      is_active: Boolean(form.value.is_active),
    }

    if (isEditing) {
      if (form.value.password) payload.password = form.value.password
      await updateDoctor(editingId.value, payload, auth.accessToken)
    } else {
      payload.password = form.value.password
      await createDoctor(payload, auth.accessToken)
    }

    toast.showSuccess(isEditing ? 'Doctor profile updated.' : 'Doctor profile created.')
    resetForm()
    await loadDoctors()
  } catch (err) {
    error.value = err.message || 'Failed to save doctor'
    toast.showError(error.value)
  } finally {
    saving.value = false
  }
}

function openCreateForm() {
  showForm.value = true
  editingId.value = null
}

function consumeCreateIntent(intent) {
  if (intent !== 'create') return
  openCreateForm()
  const nextQuery = { ...route.query }
  delete nextQuery.intent
  router.replace({ query: nextQuery })
}

async function removeDoctor(id) {
  if (!window.confirm('Delete this doctor?')) return
  try {
    await deleteDoctor(id, auth.accessToken)
    toast.showSuccess('Doctor deleted.')
    await loadDoctors()
  } catch (err) {
    error.value = err.message || 'Failed to delete doctor'
    toast.showError(error.value)
  }
}

watch(
  () => route.query.intent,
  (intent) => {
    consumeCreateIntent(intent)
  },
  { immediate: true }
)

onMounted(loadDoctors)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">Doctors Management</h1>
        <p class="page-subtitle">Create and maintain doctor profiles, department mapping, and availability status.</p>
      </div>
      <button class="btn primary" @click="openCreateForm">Add Doctor</button>
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
        <label>Department</label>
        <select v-model="form.department_id">
          <option value="">Select department</option>
          <option v-for="department in departments" :key="department.id" :value="department.id">
            {{ department.name }}
          </option>
        </select>
        <small v-if="form.department_id" class="muted department-meta">
          <DepartmentIcon :department-name="departments.find((item) => item.id === Number(form.department_id))?.name" />
          <span>{{ departments.find((item) => item.id === Number(form.department_id))?.name }}</span>
        </small>
      </div>
      <div class="form-row">
        <label>License Number</label>
        <input v-model.trim="form.license_number" />
      </div>
      <div class="form-row">
        <label>Contact Number</label>
        <input v-model.trim="form.contact_number" />
      </div>
      <div class="form-row">
        <label>Experience (Years)</label>
        <input v-model="form.years_experience" type="number" min="0" max="80" />
      </div>
      <div class="form-row form-row-full">
        <label>Bio</label>
        <textarea v-model="form.bio" rows="3" />
      </div>
      <div class="form-row checkbox-row">
        <label>
          <input v-model="form.is_active" type="checkbox" /> Active
        </label>
      </div>
      <div class="button-row">
        <button class="btn primary" :disabled="saving">{{ saving ? 'Saving...' : submitLabel }}</button>
        <button class="btn" type="button" @click="resetForm">Cancel</button>
      </div>
    </form>

    <div class="card stack-md">
      <div class="toolbar">
        <input v-model.trim="search" placeholder="Search doctor by name/email" @keyup.enter="loadDoctors" />
        <select v-model="departmentFilter">
          <option value="">All Departments</option>
          <option v-for="department in departments" :key="department.id" :value="department.id">
            {{ department.name }}
          </option>
        </select>
        <small v-if="departmentFilter" class="muted department-meta">
          <DepartmentIcon :department-name="departments.find((item) => item.id === Number(departmentFilter))?.name" />
          <span>{{ departments.find((item) => item.id === Number(departmentFilter))?.name }}</span>
        </small>
        <button class="btn" @click="loadDoctors">Search</button>
        <p class="muted">{{ doctors.length }} records</p>
      </div>

      <div v-if="error" class="alert error">{{ error }}</div>
      <p v-if="loading">Loading doctors...</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Doctor</th>
            <th>Department</th>
            <th>Contact</th>
            <th>Experience (Years)</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doctor in doctors" :key="doctor.id">
            <td>
              <div class="person-cell">
                <img :src="avatarUrl(doctor.id)" alt="Doctor profile" class="avatar" />
                <div>
                  <p class="person-name">{{ doctor.name }}</p>
                  <p class="muted">{{ doctor.email }}</p>
                </div>
              </div>
            </td>
            <td>
              <span v-if="doctor.department_name" class="department-meta">
                <DepartmentIcon :department-name="doctor.department_name" />
                <span>{{ doctor.department_name }}</span>
              </span>
              <span v-else>-</span>
            </td>
            <td>{{ doctor.contact_number || '-' }}</td>
            <td>{{ doctor.years_experience ?? '-' }} years</td>
            <td><span class="badge" :class="doctor.is_active ? 'ok' : 'warn'">{{ doctor.is_active ? 'Active' : 'Inactive' }}</span></td>
            <td class="actions-cell">
              <button class="btn small" @click="startEdit(doctor)">Edit</button>
              <button class="btn small danger" @click="removeDoctor(doctor.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
