<script setup>
import { computed } from 'vue'
import { onMounted, ref } from 'vue'
import DepartmentIcon from '@/components/DepartmentIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { useDoctorStore } from '@/stores/doctor'

const auth = useAuthStore()
const doctorStore = useDoctorStore()
const error = ref('')
const doctorAvatarUrl = computed(() => {
  const id = doctorStore.profile?.id || auth.user?.id || 'profile'
  return `https://picsum.photos/seed/doctor-${id}/56/56`
})

async function loadProfile() {
  error.value = ''
  try {
    await doctorStore.fetchProfile(auth.accessToken)
  } catch (err) {
    error.value = err.message || 'Failed to load doctor profile'
  }
}

onMounted(loadProfile)
</script>

<template>
  <section class="stack-lg">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Profile</h1>
        <p class="page-subtitle">View your account details and professional profile.</p>
      </div>
    </div>

    <div v-if="error" class="alert error">{{ error }}</div>

    <article class="card stack-md" v-if="doctorStore.profile">
      <div class="person-cell">
        <img :src="doctorAvatarUrl" alt="Doctor profile" class="avatar" />
        <div>
          <p class="person-name">{{ doctorStore.profile.name || '-' }}</p>
          <p class="muted">{{ doctorStore.profile.email }}</p>
        </div>
      </div>
      <div class="dashboard-grid">
        <article class="card stack-md">
          <h3>Professional Details</h3>
          <p><strong>Role:</strong> {{ doctorStore.profile.type || '-' }}</p>
          <p><strong>Status:</strong> {{ doctorStore.profile.is_active ? 'Active' : 'Inactive' }}</p>
          <p class="department-meta">
            <DepartmentIcon :department-name="doctorStore.profile.department_name" />
            <strong>Department:</strong>
            <span>{{ doctorStore.profile.department_name || '-' }}</span>
          </p>
          <p><strong>Experience:</strong> {{ doctorStore.profile.years_experience ?? '-' }} years</p>
          <p><strong>License:</strong> {{ doctorStore.profile.license_number || '-' }}</p>
        </article>
        <article class="card stack-md">
          <h3>Contact & Bio</h3>
          <p><strong>Contact:</strong> {{ doctorStore.profile.contact_number || '-' }}</p>
          <p><strong>Bio:</strong> {{ doctorStore.profile.bio || '-' }}</p>
        </article>
      </div>
    </article>

    <p v-else-if="doctorStore.loadingProfile">Loading profile...</p>
  </section>
</template>
