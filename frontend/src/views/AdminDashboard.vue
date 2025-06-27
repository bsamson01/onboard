<template>
  <div class="min-h-screen bg-gray-50">

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

          <!-- Applications Tab -->
          <div v-if="activeTab === 'applications'" class="space-y-6">
            <!-- Application Metrics Overview -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div class="bg-blue-50 rounded-lg p-4">
                <h4 class="text-sm font-medium text-blue-800">Pending Review</h4>
                <p class="text-2xl font-bold text-blue-600">{{ dashboardData.pending_review_count || 0 }}</p>
                <p class="text-sm text-blue-600">Applications awaiting review</p>
              </div>
              
              <div class="bg-green-50 rounded-lg p-4">
                <h4 class="text-sm font-medium text-green-800">Approved</h4>
                <p class="text-2xl font-bold text-green-600">{{ dashboardData.approved_count || 0 }}</p>
                <p class="text-sm text-green-600">Applications approved</p>
              </div>
              
              <div class="bg-red-50 rounded-lg p-4">
                <h4 class="text-sm font-medium text-red-800">Rejected</h4>
                <p class="text-2xl font-bold text-red-600">{{ dashboardData.rejected_count || 0 }}</p>
                <p class="text-sm text-red-600">Applications rejected</p>
              </div>
              
              <div class="bg-purple-50 rounded-lg p-4">
                <h4 class="text-sm font-medium text-purple-800">Total Applications</h4>
                <p class="text-2xl font-bold text-purple-600">{{ (onboardingCount + loanCount) || 0 }}</p>
                <p class="text-sm text-purple-600">All application types</p>
              </div>
            </div>
            
            <!-- Application Review Interface -->
            <div class="bg-white rounded-lg shadow">
              <!-- Sub-Tab Navigation -->
              <div class="border-b border-gray-200">
                <nav class="-mb-px flex space-x-8 px-6 pt-6">
                  <button 
                    @click="applicationTab = 'onboarding'"
                    :class="[
                      'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                      applicationTab === 'onboarding' 
                        ? 'border-blue-500 text-blue-600' 
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    ]"
                  >
                    Onboarding Applications
                    <span v-if="onboardingCount > 0" class="ml-2 bg-blue-100 text-blue-600 py-0.5 px-2 rounded-full text-xs font-medium">{{ onboardingCount }}</span>
                  </button>
                  <button 
                    @click="applicationTab = 'loan'"
                    :class="[
                      'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                      applicationTab === 'loan' 
                        ? 'border-blue-500 text-blue-600' 
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    ]"
                  >
                    Loan Applications
                    <span v-if="loanCount > 0" class="ml-2 bg-blue-100 text-blue-600 py-0.5 px-2 rounded-full text-xs font-medium">{{ loanCount }}</span>
                  </button>
                </nav>
              </div>
              
              <!-- Sub-Tab Content -->
              <div class="p-6">
                <!-- Onboarding Applications Sub-Tab -->
                <div v-if="applicationTab === 'onboarding'">
                  <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-medium text-gray-900">Onboarding Applications</h3>
                    <button @click="loadApplications('onboarding')" class="text-blue-600 hover:text-blue-800 text-sm">
                      <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Refresh
                    </button>
                  </div>
                  <div v-if="isLoadingApplications" class="flex justify-center items-center py-12">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                  <div v-else class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                      <thead class="bg-gray-50">
                        <tr>
                          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Submitted</th>
                          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody class="bg-white divide-y divide-gray-200">
                        <tr v-for="app in onboardingApplications" :key="app.id" class="hover:bg-gray-50">
                          <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm font-medium text-gray-900">{{ app.application_number }}</div>
                            <div class="text-sm text-gray-500">{{ app.loan_type }}</div>
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                                  :class="getStatusBadgeClass(app.status_display?.color || 'blue')">
                              {{ app.status_display?.label || app.status }}
                            </span>
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {{ formatDate(app.submitted_at || app.created_at) }}
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-3">
                            <button @click="viewApplication(app)" class="text-blue-600 hover:text-blue-900">View</button>
                            <button @click="openStatusModal(app)" class="text-green-600 hover:text-green-900">Update Status</button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <div v-if="onboardingApplications.length === 0" class="text-center py-12 text-gray-500">
                      No onboarding applications ready for review.
                    </div>
                  </div>
                </div>
                
                <!-- Loan Applications Sub-Tab -->
                <div v-if="applicationTab === 'loan'">
                  <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-medium text-gray-900">Loan Applications</h3>
                    <button @click="loadApplications('loan')" class="text-blue-600 hover:text-blue-800 text-sm">
                      <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Refresh
                    </button>
                  </div>
                  <div v-if="isLoadingApplications" class="flex justify-center items-center py-12">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                  <div v-else class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                      <thead class="bg-gray-50">
                        <tr>
                          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount & Type</th>
                          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Submitted</th>
                          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody class="bg-white divide-y divide-gray-200">
                        <tr v-for="app in loanApplications" :key="app.id" class="hover:bg-gray-50">
                          <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm font-medium text-gray-900">{{ app.application_number }}</div>
                            <div class="text-sm text-gray-500">ID: {{ app.id.slice(0, 8) }}...</div>
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm font-medium text-gray-900">${{ formatCurrency(app.requested_amount) }}</div>
                            <div class="text-sm text-gray-500">{{ app.loan_type }}</div>
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                                  :class="getStatusBadgeClass(app.status_display?.color || 'blue')">
                              {{ app.status_display?.label || app.status }}
                            </span>
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {{ formatDate(app.submitted_at || app.created_at) }}
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-3">
                            <button @click="viewLoanApplication(app)" class="text-blue-600 hover:text-blue-900">View</button>
                            <button @click="openStatusModal(app)" class="text-green-600 hover:text-green-900">Update Status</button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <div v-if="loanApplications.length === 0" class="text-center py-12 text-gray-500">
                      No loan applications ready for review.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Users Tab -->
          <div v-if="isAdmin && activeTab === 'users'" class="space-y-6">
            <UsersPanel :users="users" :isAdmin="isAdmin" @refresh="loadUsers" @delete="deleteUser" />
          </div>

          <!-- Audit Logs Tab -->
          <div v-if="isAdmin && activeTab === 'logs'" class="space-y-6">
            <AuditLogsPanel :logs="auditLogs" @refresh="loadAuditLogs" />
          </div>
        </div>
      </div>
    </div>

    <!-- Configuration Modal -->
    <ServiceConfigModal
      v-if="isAdmin && showConfigModal"
      :service="selectedService"
      @close="showConfigModal = false"
      @save="saveConfiguration"
    />

    <!-- Application Details Modal -->
    <div v-if="selectedApplication" class="fixed inset-0 bg-gray-600 bg-opacity-50 z-50 flex items-center justify-center">
      <div class="relative mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white overflow-x-auto max-h-screen overflow-y-auto flex flex-col">
        <div class="mt-3">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-medium text-gray-900">Application #{{ selectedApplication.application_number }}</h3>
            <button @click="closeApplicationModal" class="text-gray-400 hover:text-gray-600">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          
          <!-- Onboarding Application Details -->
          <div v-if="applicationDetails && selectedOnboardingDetails" class="space-y-6">
            <div class="bg-gray-50 p-4 rounded-lg">
              <h4 class="font-medium text-gray-900 mb-3">Onboarding Application Information</h4>
              <dl class="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
                <div>
                  <dt class="text-sm font-medium text-gray-500">Status</dt>
                  <dd class="mt-1">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                          :class="getStatusBadgeClass(applicationDetails.status_display?.color || 'blue')">
                      {{ applicationDetails.status_display?.label || selectedOnboardingDetails.status }}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Submitted</dt>
                  <dd class="mt-1 text-sm text-gray-900">{{ formatDate(selectedOnboardingDetails.submitted_at) }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Progress</dt>
                  <dd class="mt-1 text-sm text-gray-900">{{ selectedOnboardingDetails.progress_percentage }}% Complete</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Current Step</dt>
                  <dd class="mt-1 text-sm text-gray-900">{{ selectedOnboardingDetails.current_step }}/{{ selectedOnboardingDetails.total_steps }}</dd>
                </div>
              </dl>
            </div>
          </div>
          
          <!-- Loan Application Details -->
          <div v-if="applicationDetails && selectedLoanDetails" class="space-y-6">
            <div class="bg-gray-50 p-4 rounded-lg">
              <h4 class="font-medium text-gray-900 mb-3">Loan Application Information</h4>
              <dl class="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
                <div>
                  <dt class="text-sm font-medium text-gray-500">Status</dt>
                  <dd class="mt-1">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                          :class="getStatusBadgeClass(applicationDetails.status_display?.color || 'blue')">
                      {{ applicationDetails.status_display?.label || selectedLoanDetails.status }}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Requested Amount</dt>
                  <dd class="mt-1 text-sm text-gray-900">${{ formatCurrency(selectedLoanDetails.requested_amount) }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Loan Type</dt>
                  <dd class="mt-1 text-sm text-gray-900">{{ selectedLoanDetails.loan_type }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500">Submitted</dt>
                  <dd class="mt-1 text-sm text-gray-900">{{ formatDate(selectedLoanDetails.submitted_at) }}</dd>
                </div>
              </dl>
            </div>
          </div>
          
          <div class="flex justify-end space-x-3 mt-6 pt-4 border-t">
            <button @click="closeApplicationModal" class="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
            <button @click="openStatusModal(selectedApplication)" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Update Status</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Status Update Modal -->
    <div v-if="showStatusModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
      <div class="relative mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Update Application Status</h3>
        <div v-if="allowedTransitions.length > 0">
          <select v-model="statusUpdateForm.status" class="w-full mb-4 rounded-md border-gray-300">
            <option value="" disabled>Select new status</option>
            <option v-for="status in allowedTransitions" :key="status" :value="status">{{ status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) }}</option>
          </select>
          <textarea v-if="['rejected', 'cancelled'].includes(statusUpdateForm.status)" v-model="statusUpdateForm.reason" class="w-full mb-4 rounded-md border-gray-300" placeholder="Reason (required for rejection)"></textarea>
          <button @click="updateStatus" :disabled="!statusUpdateForm.status || (['rejected', 'cancelled'].includes(statusUpdateForm.status) && !statusUpdateForm.reason)" class="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400">Update Status</button>
        </div>
        <div v-else class="text-gray-500">No status transitions available.</div>
        <button @click="closeStatusModal" class="mt-4 w-full px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
      </div>
    </div>

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
const applicationTab = ref('onboarding')
const isLoading = ref(false)
const isLoadingApplications = ref(false)
const alertMessage = ref('')
const alertType = ref('success')
const showConfigModal = ref(false)
const selectedService = ref(null)

// Application data
const onboardingApplications = ref([])
const loanApplications = ref([])
const onboardingCount = ref(0)
const loanCount = ref(0)

// Modal state
const selectedApplication = ref(null)
const applicationDetails = ref(null)
const showStatusModal = ref(false)
const allowedTransitions = ref([])
const statusUpdateForm = ref({ application: null, status: '', reason: '', notes: '' })
const selectedOnboardingDetails = ref(null)
const selectedLoanDetails = ref(null)

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

const isAdmin = computed(() => authStore.user?.role === 'admin')

const tabs = [
  { id: 'health', name: 'System Health' },
  { id: 'services', name: 'External Services' },
  { id: 'applications', name: 'Applications' },
]
if (isAdmin.value) {
  tabs.push({ id: 'users', name: 'Users' })
  tabs.push({ id: 'logs', name: 'Audit Logs' })
}

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

const navigateToApplications = (status = null) => {
  if (status) {
    router.push(`/applications?status=${status}`)
  } else {
    router.push('/applications')
  }
}

// Application management methods
const loadApplications = async (type = null) => {
  try {
    isLoadingApplications.value = true
    const params = new URLSearchParams({ 
      limit: '50', 
      offset: '0'
    })
    
    if (type) {
      params.append('application_type', type)
    }
    
    const response = await api.get(`/status/admin/applications?${params}`)
    const applications = response.data.applications || []
    
    if (type === 'onboarding' || !type) {
      onboardingApplications.value = applications.filter(app => app.loan_type === 'Onboarding')
      onboardingCount.value = onboardingApplications.value.length
    }
    
    if (type === 'loan' || !type) {
      loanApplications.value = applications.filter(app => app.loan_type !== 'Onboarding')
      loanCount.value = loanApplications.value.length
    }
    
    if (!type) {
      onboardingApplications.value = applications.filter(app => app.loan_type === 'Onboarding')
      loanApplications.value = applications.filter(app => app.loan_type !== 'Onboarding')
      onboardingCount.value = onboardingApplications.value.length
      loanCount.value = loanApplications.value.length
    }
  } catch (error) {
    showAlert(`Failed to load ${type || 'all'} applications`, 'error')
  } finally {
    isLoadingApplications.value = false
  }
}

const viewApplication = async (application) => {
  try {
    selectedApplication.value = application
    let onboardingId = application.id
    if (application.app && application.loan_type === 'Onboarding') {
      onboardingId = application.app.id
    }
    if (application.loan_type !== 'Onboarding') {
      showAlert('This is not an onboarding application.', 'error')
      return
    }
    const detailsResponse = await api.get(`/onboarding/applications/${onboardingId}`)
    selectedOnboardingDetails.value = detailsResponse.data
    const statusResponse = await api.get(`/status/applications/${onboardingId}/status`)
    applicationDetails.value = statusResponse.data
  } catch (error) {
    showAlert('Failed to load application details', 'error')
    selectedOnboardingDetails.value = null
  }
}

const viewLoanApplication = async (application) => {
  try {
    selectedApplication.value = application
    const detailsResponse = await api.get(`/loans/applications/${application.id}`)
    selectedLoanDetails.value = detailsResponse.data
    const statusResponse = await api.get(`/status/applications/${application.id}/status`)
    applicationDetails.value = statusResponse.data
  } catch (error) {
    showAlert('Failed to load loan application details', 'error')
    selectedLoanDetails.value = null
  }
}

const openStatusModal = async (application) => {
  try {
    statusUpdateForm.value = { application, status: '', reason: '', notes: '' }
    const response = await api.get(`/status/applications/${application.id}/allowed-transitions`)
    allowedTransitions.value = response.data.allowed_transitions
    showStatusModal.value = true
    selectedApplication.value = null
  } catch (error) {
    showAlert('Failed to load status options', 'error')
  }
}

const updateStatus = async () => {
  try {
    const updateData = {
      status: statusUpdateForm.value.status,
      reason: statusUpdateForm.value.reason || null,
      notes: statusUpdateForm.value.notes || null
    }
    await api.post(`/status/applications/${statusUpdateForm.value.application.id}/update-status`, updateData)
    showAlert('Application status updated successfully', 'success')
    closeStatusModal()
    await loadApplications()
  } catch (error) {
    showAlert('Failed to update status', 'error')
  }
}

const closeApplicationModal = () => {
  selectedApplication.value = null
  applicationDetails.value = null
  selectedOnboardingDetails.value = null
  selectedLoanDetails.value = null
}

const closeStatusModal = () => {
  showStatusModal.value = false
  statusUpdateForm.value = { application: null, status: '', reason: '', notes: '' }
  allowedTransitions.value = []
}

// Utility functions
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatCurrency = (amount) => {
  if (!amount) return '0'
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

const getStatusBadgeClass = (color) => {
  const colorMap = {
    blue: 'bg-blue-100 text-blue-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    orange: 'bg-orange-100 text-orange-800',
    green: 'bg-green-100 text-green-800',
    purple: 'bg-purple-100 text-purple-800',
    red: 'bg-red-100 text-red-800',
    gray: 'bg-gray-100 text-gray-800'
  }
  return colorMap[color] || 'bg-gray-100 text-gray-800'
}

const handleLogout = () => {
  authStore.logout()
  router.push('/')
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
  await loadApplications()
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