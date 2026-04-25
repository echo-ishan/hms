<script setup>
import { onMounted, ref } from 'vue'
import { createDepartment, listDepartments } from '@/api/admin'
import DepartmentIcon from '@/components/DepartmentIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const auth = useAuthStore()
const toast = useToast()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const departments = ref([])
const form = ref({ name: '', description: '' })
const showForm = ref(false)

async function loadDepartments() {
  loading.value = true
  error.value = ''
  try {
    const data = await listDepartments(auth.accessToken)
    departments.value = data.departments
  } catch (err) {
    error.value = err.message || 'Failed to load departments'
  } finally {
    loading.value = false
  }
}

async function submitDepartment() {
  saving.value = true
  error.value = ''
  try {
    await createDepartment(
      {
        name: form.value.name,
        description: form.value.description || null,
      },
      auth.accessToken,
    )
    toast.showSuccess('Department created.')
    form.value = { name: '', description: '' }
    showForm.value = false
    await loadDepartments()
  } catch (err) {
    error.value = err.message || 'Failed to create department'
    toast.showError(error.value)
  } finally {
    saving.value = false
  }
}

function openCreateForm() {
  showForm.value = true
  error.value = ''
}

function closeCreateForm() {
  showForm.value = false
  form.value = { name: '', description: '' }
}

onMounted(loadDepartments)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">Departments</h1>
        <p class="page-subtitle">Manage clinical departments and maintain organizational metadata.</p>
      </div>
      <button class="btn primary" @click="openCreateForm">Add Department</button>
    </div>

    <form v-if="showForm" class="card stack-md" @submit.prevent="submitDepartment">
      <h3>Add Department</h3>
      <div class="form-row">
        <label>Name</label>
        <input v-model.trim="form.name" required />
      </div>
      <div class="form-row">
        <label>Description</label>
        <textarea v-model="form.description" rows="3" />
      </div>
      <div class="button-row">
        <button class="btn primary" :disabled="saving">{{ saving ? 'Saving...' : 'Create Department' }}</button>
        <button class="btn" type="button" @click="closeCreateForm">Cancel</button>
      </div>
      <p v-if="error" class="alert error">{{ error }}</p>
    </form>

    <div class="card stack-md">
      <h3>Department List</h3>
      <p v-if="loading">Loading departments...</p>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Description</th>
            <th>Doctors</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="department in departments" :key="department.id">
            <td>
              <span class="department-meta">
                <DepartmentIcon :department-name="department.name" />
                <span>{{ department.name }}</span>
              </span>
            </td>
            <td>{{ department.description || '-' }}</td>
            <td>{{ department.doctor_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
