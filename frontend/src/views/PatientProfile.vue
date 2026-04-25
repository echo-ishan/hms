<script setup>
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { usePatientStore } from '@/stores/patient'

const auth = useAuthStore()
const patientStore = usePatientStore()
const toast = useToast()
const error = ref('')
const saving = ref(false)
const editing = ref(false)

const genderOptions = ['Male', 'Female', 'Other']

const form = ref({
  name: '',
  dob: '',
  contact_number: '',
  gender: '',
  blood_group: '',
  emergency_contact: '',
  address: '',
  past_medical_history: '',
  password: '',
})

const avatarUrl = `https://picsum.photos/seed/patient-${auth.user?.id || 'profile'}/56/56`

const canEdit = computed(() => Boolean(patientStore.profile))

function hydrateForm(profile) {
  form.value = {
    name: profile?.name || '',
    dob: profile?.dob || '',
    contact_number: profile?.contact_number || '',
    gender: profile?.gender || '',
    blood_group: profile?.blood_group || '',
    emergency_contact: profile?.emergency_contact || '',
    address: profile?.address || '',
    past_medical_history: profile?.past_medical_history || '',
    password: '',
  }
}

function startEdit() {
  if (!patientStore.profile) return
  hydrateForm(patientStore.profile)
  editing.value = true
}

function cancelEdit() {
  if (patientStore.profile) hydrateForm(patientStore.profile)
  editing.value = false
}

async function saveProfile() {
  if (!patientStore.profile) return
  saving.value = true
  error.value = ''
  try {
    const payload = {
      name: form.value.name,
      dob: form.value.dob,
      contact_number: form.value.contact_number,
      gender: form.value.gender || null,
      blood_group: form.value.blood_group || null,
      emergency_contact: form.value.emergency_contact || null,
      address: form.value.address || null,
      past_medical_history: form.value.past_medical_history || null,
    }
    if (form.value.password) payload.password = form.value.password
    await patientStore.updateProfile(payload, auth.accessToken)
    editing.value = false
    toast.showSuccess('Profile updated successfully.')
  } catch (err) {
    const message = err.message || 'Failed to update profile'
    error.value = message
    toast.showError(message)
  } finally {
    saving.value = false
  }
}

async function loadProfile() {
  error.value = ''
  try {
    await patientStore.fetchProfile(auth.accessToken)
    if (patientStore.profile) hydrateForm(patientStore.profile)
  } catch (err) {
    error.value = err.message || 'Failed to load patient profile'
  }
}

onMounted(loadProfile)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Profile</h1>
        <p class="page-subtitle">View and update your account and medical profile details.</p>
      </div>
      <button v-if="canEdit && !editing" class="btn primary" @click="startEdit">Edit Profile</button>
    </div>

    <div v-if="error" class="alert error">{{ error }}</div>

    <article class="card stack-md" v-if="patientStore.profile && !editing">
      <div class="person-cell">
        <img :src="avatarUrl" alt="Patient profile" class="avatar" />
        <div>
          <p class="person-name">{{ patientStore.profile.name || '-' }}</p>
          <p class="muted">{{ patientStore.profile.email }}</p>
        </div>
      </div>
      <p><strong>Date of Birth:</strong> {{ patientStore.profile.dob || '-' }}</p>
      <p><strong>Gender:</strong> {{ patientStore.profile.gender || '-' }}</p>
      <p><strong>Blood Group:</strong> {{ patientStore.profile.blood_group || '-' }}</p>
      <p><strong>Contact:</strong> {{ patientStore.profile.contact_number || '-' }}</p>
      <p><strong>Emergency Contact:</strong> {{ patientStore.profile.emergency_contact || '-' }}</p>
      <p><strong>Address:</strong> {{ patientStore.profile.address || '-' }}</p>
      <p><strong>Past Medical History:</strong> {{ patientStore.profile.past_medical_history || '-' }}</p>
      <p><strong>Status:</strong> {{ patientStore.profile.is_active ? 'Active' : 'Inactive' }}</p>
    </article>

    <form v-else-if="patientStore.profile && editing" class="card form-grid" @submit.prevent="saveProfile">
      <h3 class="form-row-full">Edit Profile</h3>

      <div class="form-row">
        <label>Name</label>
        <input v-model.trim="form.name" required />
      </div>

      <div class="form-row">
        <label>Email</label>
        <input :value="patientStore.profile.email" type="email" disabled />
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

      <div class="form-row">
        <label>New Password (optional)</label>
        <input v-model="form.password" type="password" minlength="6" />
      </div>

      <div class="form-row form-row-full">
        <label>Address</label>
        <textarea v-model="form.address" rows="2" />
      </div>

      <div class="form-row form-row-full">
        <label>Past Medical History</label>
        <textarea v-model="form.past_medical_history" rows="3" />
      </div>

      <div class="button-row">
        <button class="btn primary" :disabled="saving">{{ saving ? 'Saving...' : 'Save Changes' }}</button>
        <button class="btn" type="button" @click="cancelEdit">Cancel</button>
      </div>
    </form>

    <p v-else-if="patientStore.loadingProfile">Loading profile...</p>
  </section>
</template>
