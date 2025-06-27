<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <h1 class="text-3xl font-bold text-gray-900">Staff Dashboard</h1>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-500">Welcome, {{ authStore.user?.first_name }}</span>
            <button @click="handleLogout" class="btn-secondary">Logout</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <h3 class="text-sm font-medium text-gray-500">Active Applications</h3>
          <p class="text-3xl font-bold text-green-600">{{ dashboardData.active_applications || 0 }}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <h3 class="text-sm font-medium text-gray-500">Recent Activities</h3>
          <ul class="mt-2 space-y-2">
            <li v-for="activity in dashboardData.recent_activities || []" :key="activity.id" class="text-sm text-gray-700">
              {{ activity.description }} <span class="text-gray-400">({{ formatDate(activity.timestamp) }})</span>
            </li>
            <li v-if="!dashboardData.recent_activities || dashboardData.recent_activities.length === 0" class="text-gray-400">No recent activities</li>
          </ul>
        </div>
      </div>
      <!-- Add more staff-appropriate panels here -->
    </div>

    <!-- Loading Overlay -->
    <div v-if="isLoading" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-2 text-sm text-gray-600">Loading...</p>
      </div>
    </div>

    <!-- Alert Messages -->
    <div v-if="alertMessage" class="fixed top-4 right-4 z-50">
      <div class="max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto"
           :class="alertType === 'success' ? 'border-l-4 border-green-400' : 'border-l-4 border-red-400'">
        <div class="p-4">
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <svg v-if="alertType === 'success'" class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <svg v-else class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
              </svg>
            </div>
            <div class="ml-3 w-0 flex-1">
              <p class="text-sm font-medium" :class="alertType === 'success' ? 'text-green-800' : 'text-red-800'">
                {{ alertMessage }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()

const isLoading = ref(false)
const alertMessage = ref('')
const alertType = ref('success')

const dashboardData = reactive({
  active_applications: 0,
  recent_activities: []
})

const showAlert = (message, type = 'success') => {
  alertMessage.value = message
  alertType.value = type
  setTimeout(() => {
    alertMessage.value = ''
  }, 5000)
}

const formatDate = (dateString) => {
  if (!dateString) return 'Unknown time'
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadDashboard = async () => {
  try {
    isLoading.value = true
    const response = await api.get('/admin/staff/dashboard')
    Object.assign(dashboardData, response.data)
  } catch (error) {
    showAlert('Failed to load staff dashboard data', 'error')
  } finally {
    isLoading.value = false
  }
}

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}

onMounted(async () => {
  if (!authStore.isAuthenticated || !['admin', 'loan_officer', 'risk_officer'].includes(authStore.user?.role)) {
    router.push('/login')
    return
  }
  await loadDashboard()
})
</script>

<style scoped>
.btn-secondary {
  @apply inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}
.card {
  @apply bg-white shadow rounded-lg p-6;
}
</style> 