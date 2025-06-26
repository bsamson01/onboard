<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <h1 class="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-500">Welcome, {{ authStore.user?.first_name }}</span>
            <button @click="authStore.logout" class="btn-secondary">Logout</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- System Status Overview -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <h3 class="text-sm font-medium text-gray-500">Total Users</h3>
          <p class="text-3xl font-bold text-blue-600">{{ dashboardData.total_users || 0 }}</p>
        </div>
        
        <div class="bg-white rounded-lg shadow p-6">
          <h3 class="text-sm font-medium text-gray-500">Active Applications</h3>
          <p class="text-3xl font-bold text-green-600">{{ dashboardData.active_applications || 0 }}</p>
        </div>
        
        <div class="bg-white rounded-lg shadow p-6">
          <h3 class="text-sm font-medium text-gray-500">System Status</h3>
          <p class="text-lg font-semibold" :class="systemStatusClass">{{ dashboardData.system_status || 'Unknown' }}</p>
        </div>
        
        <div class="bg-white rounded-lg shadow p-6">
          <h3 class="text-sm font-medium text-gray-500">External Services</h3>
          <p class="text-lg font-semibold" :class="externalServicesStatusClass">
            {{ externalServicesStatus }}
          </p>
        </div>
      </div>

      <!-- Main Content Tabs -->
      <div class="bg-white shadow rounded-lg">
        <div class="border-b border-gray-200">
          <nav class="-mb-px flex">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'py-2 px-4 text-sm font-medium border-b-2',
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              {{ tab.name }}
            </button>
          </nav>
        </div>

        <div class="p-6">
          <!-- System Health Tab -->
          <div v-if="activeTab === 'health'" class="space-y-6">
            <SystemHealthPanel :health-data="systemHealth" @refresh="loadSystemHealth" />
          </div>

          <!-- External Services Tab -->
          <div v-if="activeTab === 'services'" class="space-y-6">
            <ExternalServicesPanel 
              :services="externalServices" 
              @configure="showConfigureModal"
              @test="testConnection"
              @refresh="loadExternalServices"
            />
          </div>

          <!-- Users Tab -->
          <div v-if="activeTab === 'users'" class="space-y-6">
            <UsersPanel :users="users" @refresh="loadUsers" @delete="deleteUser" />
          </div>

          <!-- Audit Logs Tab -->
          <div v-if="activeTab === 'logs'" class="space-y-6">
            <AuditLogsPanel :logs="auditLogs" @refresh="loadAuditLogs" />
          </div>
        </div>
      </div>
    </div>

    <!-- Configuration Modal -->
    <ServiceConfigModal
      v-if="showConfigModal"
      :service="selectedService"
      @close="showConfigModal = false"
      @save="saveConfiguration"
    />

    <!-- Loading Overlay -->
    <div v-if="isLoading" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-2 text-sm text-gray-600">Loading...</p>
      </div>
    </div>

    <!-- Alert Messages -->
    <div v-if="alertMessage" class="fixed bottom-4 right-4 z-50">
      <div :class="[
        'rounded-md p-4 shadow-lg',
        alertType === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
      ]">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg v-if="alertType === 'success'" class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <svg v-else class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L10 11.414l1.293-1.293a1 1 0 001.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p :class="[
              'text-sm font-medium',
              alertType === 'success' ? 'text-green-800' : 'text-red-800'
            ]">
              {{ alertMessage }}
            </p>
          </div>
          <div class="ml-auto pl-3">
            <button @click="alertMessage = ''" class="text-gray-400 hover:text-gray-600">
              <span class="sr-only">Dismiss</span>
              <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

// Components
import SystemHealthPanel from '@/components/admin/SystemHealthPanel.vue'
import ExternalServicesPanel from '@/components/admin/ExternalServicesPanel.vue'
import UsersPanel from '@/components/admin/UsersPanel.vue'
import AuditLogsPanel from '@/components/admin/AuditLogsPanel.vue'
import ServiceConfigModal from '@/components/admin/ServiceConfigModal.vue'

const router = useRouter()
const authStore = useAuthStore()

// Reactive data
const activeTab = ref('health')
const isLoading = ref(false)
const alertMessage = ref('')
const alertType = ref('success')
const showConfigModal = ref(false)
const selectedService = ref(null)

const dashboardData = reactive({
  system_status: 'operational',
  total_users: 0,
  active_applications: 0,
  recent_activities: [],
  system_health: {},
  configuration_status: {}
})

const systemHealth = ref({})
const externalServices = ref({})
const users = ref([])
const auditLogs = ref([])

// Computed properties
const systemStatusClass = computed(() => {
  switch (dashboardData.system_status) {
    case 'operational': return 'text-green-600'
    case 'degraded': return 'text-yellow-600'
    case 'unhealthy': return 'text-red-600'
    default: return 'text-gray-600'
  }
})

const externalServicesStatus = computed(() => {
  if (!externalServices.value.scorecard_service) return 'Unknown'
  return externalServices.value.scorecard_service.health_status?.status || 'Unknown'
})

const externalServicesStatusClass = computed(() => {
  const status = externalServicesStatus.value
  switch (status) {
    case 'healthy': return 'text-green-600'
    case 'unhealthy': return 'text-red-600'
    case 'not_configured': return 'text-yellow-600'
    default: return 'text-gray-600'
  }
})

const tabs = [
  { id: 'health', name: 'System Health' },
  { id: 'services', name: 'External Services' },
  { id: 'users', name: 'Users' },
  { id: 'logs', name: 'Audit Logs' }
]

// Methods
const loadDashboard = async () => {
  try {
    isLoading.value = true
    const response = await api.get('/admin/dashboard')
    Object.assign(dashboardData, response.data)
  } catch (error) {
    showAlert('Failed to load dashboard data', 'error')
  } finally {
    isLoading.value = false
  }
}

const loadSystemHealth = async () => {
  try {
    const response = await api.get('/admin/system-health')
    systemHealth.value = response.data
  } catch (error) {
    showAlert('Failed to load system health', 'error')
  }
}

const loadExternalServices = async () => {
  try {
    const response = await api.get('/admin/external-services')
    externalServices.value = response.data
  } catch (error) {
    showAlert('Failed to load external services', 'error')
  }
}

const loadUsers = async () => {
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } catch (error) {
    showAlert('Failed to load users', 'error')
  }
}

const loadAuditLogs = async () => {
  try {
    const response = await api.get('/admin/audit-logs')
    auditLogs.value = response.data.logs
  } catch (error) {
    showAlert('Failed to load audit logs', 'error')
  }
}

const showConfigureModal = (service) => {
  selectedService.value = service
  showConfigModal.value = true
}

const saveConfiguration = async (config) => {
  try {
    isLoading.value = true
    const response = await api.post('/admin/external-services/scorecard/configure', config)
    
    if (response.data.success) {
      showAlert('Configuration updated successfully', 'success')
      await loadExternalServices()
    } else {
      showAlert('Configuration update failed', 'error')
    }
  } catch (error) {
    showAlert(error.response?.data?.detail || 'Configuration update failed', 'error')
  } finally {
    isLoading.value = false
    showConfigModal.value = false
  }
}

const testConnection = async (serviceName) => {
  try {
    isLoading.value = true
    const response = await api.post(`/admin/external-services/${serviceName}/test`)
    
    if (response.data.success) {
      showAlert(`${serviceName} connection test successful`, 'success')
    } else {
      showAlert(`${serviceName} connection test failed: ${response.data.error}`, 'error')
    }
  } catch (error) {
    showAlert('Connection test failed', 'error')
  } finally {
    isLoading.value = false
  }
}

const deleteUser = async (userId) => {
  if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
    return
  }
  
  try {
    isLoading.value = true
    await api.delete(`/admin/users/${userId}`)
    showAlert('User deleted successfully', 'success')
    await loadUsers()
  } catch (error) {
    showAlert(error.response?.data?.detail || 'Failed to delete user', 'error')
  } finally {
    isLoading.value = false
  }
}

const showAlert = (message, type = 'success') => {
  alertMessage.value = message
  alertType.value = type
  setTimeout(() => {
    alertMessage.value = ''
  }, 5000)
}

// Check authentication and authorization
const checkAccess = () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  if (authStore.user?.role !== 'admin') {
    router.push('/')
    showAlert('Access denied. Admin privileges required.', 'error')
    return
  }
}

// Lifecycle
onMounted(async () => {
  checkAccess()
  await loadDashboard()
  await loadSystemHealth()
  await loadExternalServices()
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