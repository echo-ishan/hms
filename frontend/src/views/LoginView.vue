<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const toast = useToast()

const form = reactive({
  email: '',
  password: '',
})

const errorMessage = ref('')
const submitting = ref(false)

async function handleSubmit() {
  errorMessage.value = ''
  submitting.value = true

  try {
    const user = await auth.login({
      email: form.email,
      password: form.password,
    })
    toast.showSuccess('Logged in successfully.')

    const redirectPath = typeof route.query.redirect === 'string' ? route.query.redirect : ''

    if (user?.type === 'admin') {
      await router.push(redirectPath || '/admin/dashboard')
      return
    }

    if (user?.type === 'doctor') {
      await router.push(redirectPath || '/doctor/dashboard')
      return
    }

    if (user?.type === 'patient') {
      await router.push(redirectPath || '/patient/dashboard')
      return
    }

    await router.push('/')
  } catch (error) {
    errorMessage.value = error?.message || 'Login failed. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="centered-page card stack-lg">
    <div class="stack-md">
      <h2>Login</h2>
      <p class="muted">Sign in to continue to your account.</p>
    </div>

    <p v-if="errorMessage" class="alert error">{{ errorMessage }}</p>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="form-row form-row-full">
        <span>Email</span>
        <input v-model="form.email" type="email" required autocomplete="email" />
      </label>

      <label class="form-row form-row-full">
        <span>Password</span>
        <input v-model="form.password" type="password" required autocomplete="current-password" />
      </label>

      <div class="button-row">
        <button class="btn primary" type="submit" :disabled="submitting">
          {{ submitting ? 'Signing in...' : 'Login' }}
        </button>
        <RouterLink to="/" class="btn">Back Home</RouterLink>
      </div>
    </form>

    <p class="muted">
      No account yet?
      <RouterLink to="/register" class="text-link">Create one</RouterLink>
    </p>
  </section>
</template>
