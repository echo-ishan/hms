import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import AdminDashboard from '@/views/AdminDashboard.vue'
import AdminDoctors from '@/views/AdminDoctors.vue'
import AdminPatients from '@/views/AdminPatients.vue'
import AdminDepartments from '@/views/AdminDepartments.vue'
import AdminAppointments from '@/views/AdminAppointments.vue'
import DoctorDashboard from '@/views/DoctorDashboard.vue'
import DoctorAppointments from '@/views/DoctorAppointments.vue'
import DoctorAvailability from '@/views/DoctorAvailability.vue'
import DoctorProfile from '@/views/DoctorProfile.vue'
import DoctorPatientHistory from '@/views/DoctorPatientHistory.vue'
import PatientDashboard from '@/views/PatientDashboard.vue'
import PatientAppointments from '@/views/PatientAppointments.vue'
import PatientHistory from '@/views/PatientHistory.vue'
import PatientProfile from '@/views/PatientProfile.vue'
import ForbiddenView from '@/views/ForbiddenView.vue'
import { useAuthStore } from '@/stores/auth'

function hasToken() {
  return Boolean(localStorage.getItem('hms_access_token'))
}

function hasAdminRole() {
  return localStorage.getItem('hms_user_role') === 'admin'
}

function hasDoctorRole() {
  return localStorage.getItem('hms_user_role') === 'doctor'
}

function hasPatientRole() {
  return localStorage.getItem('hms_user_role') === 'patient'
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: 'Home' },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { title: 'Login', requiresGuest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { title: 'Register', requiresGuest: true },
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: AdminDashboard,
      meta: { title: 'Dashboard', requiresAdmin: true },
    },
    {
      path: '/admin/doctors',
      name: 'admin-doctors',
      component: AdminDoctors,
      meta: { title: 'Doctors', requiresAdmin: true },
    },
    {
      path: '/admin/patients',
      name: 'admin-patients',
      component: AdminPatients,
      meta: { title: 'Patients', requiresAdmin: true },
    },
    {
      path: '/admin/departments',
      name: 'admin-departments',
      component: AdminDepartments,
      meta: { title: 'Departments', requiresAdmin: true },
    },
    {
      path: '/admin/appointments',
      name: 'admin-appointments',
      component: AdminAppointments,
      meta: { title: 'Appointments', requiresAdmin: true },
    },
    {
      path: '/doctor/dashboard',
      name: 'doctor-dashboard',
      component: DoctorDashboard,
      meta: { title: 'Dashboard', requiresDoctor: true },
    },
    {
      path: '/doctor/appointments',
      name: 'doctor-appointments',
      component: DoctorAppointments,
      meta: { title: 'Appointments', requiresDoctor: true },
    },
    {
      path: '/doctor/availability',
      name: 'doctor-availability',
      component: DoctorAvailability,
      meta: { title: 'Availability', requiresDoctor: true },
    },
    {
      path: '/doctor/profile',
      name: 'doctor-profile',
      component: DoctorProfile,
      meta: { title: 'Profile', requiresDoctor: true },
    },
    {
      path: '/doctor/patient-history',
      name: 'doctor-patient-history',
      component: DoctorPatientHistory,
      meta: { title: 'Patient History', requiresDoctor: true },
    },
    {
      path: '/patient/dashboard',
      name: 'patient-dashboard',
      component: PatientDashboard,
      meta: { title: 'Dashboard', requiresPatient: true },
    },
    {
      path: '/patient/appointments',
      name: 'patient-appointments',
      component: PatientAppointments,
      meta: { title: 'Appointments', requiresPatient: true },
    },
    {
      path: '/patient/history',
      name: 'patient-history',
      component: PatientHistory,
      meta: { title: 'History', requiresPatient: true },
    },
    {
      path: '/patient/profile',
      name: 'patient-profile',
      component: PatientProfile,
      meta: { title: 'Profile', requiresPatient: true },
    },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: ForbiddenView,
      meta: { title: 'Access Restricted' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.isBootstrapped && hasToken()) {
    await auth.bootstrap()
  }

  if (to.meta.requiresAdmin && !hasToken()) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.requiresDoctor && !hasToken()) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.requiresPatient && !hasToken()) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.requiresAdmin && !hasAdminRole()) {
    return { name: 'forbidden', query: { reason: 'admin_only' } }
  }

  if (to.meta.requiresDoctor && !hasDoctorRole()) {
    return { name: 'forbidden', query: { reason: 'doctor_only' } }
  }

  if (to.meta.requiresPatient && !hasPatientRole()) {
    return { name: 'forbidden', query: { reason: 'patient_only' } }
  }

  if (to.meta.requiresGuest && hasToken()) {
    if (hasAdminRole()) return { name: 'admin-dashboard' }
    if (hasDoctorRole()) return { name: 'doctor-dashboard' }
    if (hasPatientRole()) return { name: 'patient-dashboard' }
    return { name: 'home' }
  }

  return true
})

export default router
