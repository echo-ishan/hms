<script setup>
import { computed } from 'vue'
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToast()
const mobileOpen = ref(false)

const navItems = [
  { label: 'Dashboard', to: '/admin/dashboard' },
  { label: 'Doctors', to: '/admin/doctors' },
  { label: 'Patients', to: '/admin/patients' },
  { label: 'Departments', to: '/admin/departments' },
  { label: 'Appointments', to: '/admin/appointments' },
]

const title = computed(() => route.meta?.title || 'Admin')

function toggleSidebar() {
  mobileOpen.value = !mobileOpen.value
}

function closeSidebar() {
  mobileOpen.value = false
}

async function handleLogout() {
  await auth.logout()
  toast.showSuccess('Logged out successfully.')
  await router.push('/login')
}
</script>

<template>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <div class="top-accent" aria-hidden="true"></div>
  <div class="sidebar-overlay" :class="{ visible: mobileOpen }" @click="closeSidebar"></div>
  <div class="app-shell">
    <aside class="sidebar" :class="{ 'mobile-open': mobileOpen }">
      <h1 class="brand">HMS Admin</h1>
      <nav class="sidebar-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          active-class="is-active"
          @click="closeSidebar"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <div class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <button class="menu-toggle" @click="toggleSidebar" aria-label="Toggle navigation">
            <span></span>
            <span></span>
            <span></span>
          </button>
          <h2>{{ title }}</h2>
        </div>
        <div class="topbar-right">
          <div class="header-user">
            <img src="https://picsum.photos/seed/admin-profile/40/40" alt="Admin profile" class="avatar" />
            <span>Admin</span>
          </div>
          <button class="btn small" @click="handleLogout">Logout</button>
        </div>
      </header>
      <main id="main-content" class="content">
        <slot />
      </main>
    </div>
  </div>
</template>
