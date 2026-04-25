<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

const form = reactive({
  name: '',
  email: '',
  password: '',
  dob: '',
  contact_number: '',
  gender: '',
  blood_group: '',
  emergency_contact: '',
  address: '',
  past_medical_history: '',
})

const submitting = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  errorMessage.value = ''
  submitting.value = true

  try {
    const payload = {
      name: form.name,
      email: form.email,
      password: form.password,
      dob: form.dob,
      contact_number: form.contact_number,
      blood_group: form.blood_group || null,
      gender: form.gender || null,
      emergency_contact: form.emergency_contact || null,
      address: form.address || null,
      past_medical_history: form.past_medical_history || null,
    }

    await auth.register(payload)
    toast.showSuccess('Registration successful. Please log in.')
    await router.push({ name: 'login' })
  } catch (error) {
    errorMessage.value = error?.message || 'Registration failed. Please check your details.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="centered-page card stack-lg auth-register-card">
    <div class="stack-md">
      <h2>Create Account</h2>
      <p class="muted">Register as a patient to access your profile and appointments.</p>
    </div>

    <p v-if="errorMessage" class="alert error">{{ errorMessage }}</p>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="form-row">
        <span>Full Name</span>
        <input v-model="form.name" type="text" required autocomplete="name" />
      </label>

      <label class="form-row">
        <span>Date of Birth</span>
        <input v-model="form.dob" type="date" required />
      </label>

      <label class="form-row">
        <span>Email</span>
        <input v-model="form.email" type="email" required autocomplete="email" />
      </label>

      <label class="form-row">
        <span>Contact Number</span>
        <input v-model="form.contact_number" type="text" required autocomplete="tel" />
      </label>

      <label class="form-row form-row-full">
        <span>Password</span>
        <input v-model="form.password" type="password" required autocomplete="new-password" minlength="6" />
      </label>

      <label class="form-row">
        <span>Gender</span>
        <select v-model="form.gender">
          <option value="">Select</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
          <option value="Other">Other</option>
        </select>
      </label>

      <label class="form-row">
        <span>Blood Group</span>
        <input v-model="form.blood_group" type="text" placeholder="Optional" />
      </label>

      <label class="form-row">
        <span>Emergency Contact</span>
        <input v-model="form.emergency_contact" type="text" placeholder="Optional" />
      </label>

      <label class="form-row">
        <span>Address</span>
        <input v-model="form.address" type="text" placeholder="Optional" />
      </label>

      <label class="form-row form-row-full">
        <span>Past Medical History</span>
        <textarea v-model="form.past_medical_history" rows="3" placeholder="Optional"></textarea>
      </label>

      <div class="button-row">
        <button class="btn primary" type="submit" :disabled="submitting">
          {{ submitting ? 'Creating account...' : 'Register' }}
        </button>
        <RouterLink to="/" class="btn">Back Home</RouterLink>
      </div>
    </form>

    <p class="muted">
      Already registered?
      <RouterLink to="/login" class="text-link">Login</RouterLink>
    </p>
  </section>
</template>
