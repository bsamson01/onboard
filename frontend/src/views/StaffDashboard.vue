<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Dashboard Content -->
    <div class="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-4 sm:py-8">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-6 md:mb-8">
        <div class="bg-white rounded-lg shadow p-4 sm:p-6">
          <h3 class="text-xs sm:text-sm font-medium text-gray-500">Active Applications</h3>
          <p class="text-2xl sm:text-3xl font-bold text-green-600">{{ dashboardData.active_applications || 0 }}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-4 sm:p-6">
          <h3 class="text-xs sm:text-sm font-medium text-gray-500">Recent Activities</h3>
          <div class="relative py-4 space-y-2">
            <div v-for="activity in dashboardData.recent_activities || []" :key="activity.timestamp + activity.label" class="relative bg-white rounded-xl shadow p-4 flex flex-col gap-1 border border-gray-100">
              <div class="flex flex-wrap items-center gap-2 mb-1">
                <span :class="[
                  'inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold',
                  activity.label === 'Application Submitted' ? 'bg-blue-100 text-blue-700' :
                  activity.label === 'Application Created' ? 'bg-green-100 text-green-700' :
                  activity.label === 'Step Completed' ? 'bg-yellow-100 text-yellow-700' :
                  activity.label === 'Document Uploaded' ? 'bg-purple-100 text-purple-700' :
                  activity.label === 'Credit Score Calculated' ? 'bg-indigo-100 text-indigo-700' :
                  'bg-gray-100 text-gray-700'
                ]">
                  {{ activity.label }}
                </span>
                <span v-if="activity.user_display" class="font-bold text-sm text-gray-900">{{ activity.user_display }}</span>
                <span v-if="activity.application_number" class="px-2 py-0.5 rounded bg-gray-100 text-gray-500 text-xs font-medium">App #{{ activity.application_number }}</span>
              </div>
              <!-- <div class="text-xs sm:text-sm text-gray-700">{{ activity.description }}</div> -->
              <div class="text-xs text-gray-400 mt-1">{{ formatDate(activity.timestamp) }}</div>
            </div>
            <div v-if="!dashboardData.recent_activities || dashboardData.recent_activities.length === 0" class="text-gray-400">No recent activities</div>
          </div>
          <div v-if="dashboardData.recent_activities && dashboardData.recent_activities.length > 0" class="flex justify-end mt-2">
            <router-link to="/staff/activities" class="text-blue-600 hover:underline text-xs sm:text-sm font-medium">View All Activities</router-link>
          </div>
        </div>
      </div>
      <!-- Onboarding Applications Review Panel -->
      <div class="bg-white rounded-lg shadow p-4 sm:p-6 mt-6 sm:mt-8">
        <h3 class="text-base sm:text-lg font-medium text-gray-900 mb-4">Onboarding Applications for Review</h3>
        <div v-if="isLoadingApplications" class="flex justify-center items-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 text-xs sm:text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Submitted</th>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="app in onboardingApplications" :key="app.id" class="hover:bg-gray-50">
                <td class="px-2 sm:px-6 py-4 whitespace-nowrap">
                  <div class="text-xs sm:text-sm font-medium text-gray-900">{{ app.application_number }}</div>
                  <div class="text-xs sm:text-sm text-gray-500">ID: {{ app.id.slice(0, 8) }}...</div>
                </td>
                <td class="px-2 sm:px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {{ app.status_display.label }}
                  </span>
                </td>
                <td class="px-2 sm:px-6 py-4 whitespace-nowrap text-xs sm:text-sm text-gray-500">
                  {{ formatDate(app.submitted_at || app.created_at) }}
                </td>
                <td class="px-2 sm:px-6 py-4 whitespace-nowrap text-xs sm:text-sm font-medium space-x-2">
                  <button @click="viewApplication(app)" class="text-blue-600 hover:text-blue-900">View</button>
                  <button @click="openStatusModal(app)" class="text-green-600 hover:text-green-900">Update Status</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="onboardingApplications.length === 0" class="text-center py-8 text-gray-500">No onboarding applications found.</div>
        </div>
      </div>
      <!-- Application Details Modal -->
      <div v-if="selectedApplication" class="fixed inset-0 bg-gray-600 bg-opacity-50 z-50 flex items-center justify-center">
        <div class="relative mx-auto p-2 sm:p-5 border w-full max-w-lg sm:max-w-4xl shadow-lg rounded-md bg-white overflow-x-auto max-h-screen overflow-y-auto flex flex-col">
          <div class="mt-3">
            <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-2 sm:gap-0">
              <h3 class="text-lg sm:text-xl font-medium text-gray-900">Application #{{ selectedApplication.application_number }}</h3>
              <button @click="closeApplicationModal" class="text-gray-400 hover:text-gray-600">
                <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div v-if="applicationDetails && selectedOnboardingDetails && selectedOnboardingDetails.steps" class="space-y-6">
              <div class="bg-gray-50 p-3 sm:p-4 rounded-lg">
                <h4 class="font-medium text-gray-900 mb-3">Application Information</h4>
                <dl class="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
                  <div>
                    <dt class="text-xs sm:text-sm font-medium text-gray-500">Status</dt>
                    <dd class="mt-1">
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {{ applicationDetails.status_display.label }}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt class="text-xs sm:text-sm font-medium text-gray-500">Submitted</dt>
                    <dd class="mt-1 text-xs sm:text-sm text-gray-900">{{ formatDate(selectedApplication.submitted_at) }}</dd>
                  </div>
                  <div>
                    <dt class="text-xs sm:text-sm font-medium text-gray-500">Created</dt>
                    <dd class="mt-1 text-xs sm:text-sm text-gray-900">{{ formatDate(selectedApplication.created_at) }}</dd>
                  </div>
                </dl>
              </div>
              <!-- Show all onboarding step data -->
              <div v-for="step in selectedOnboardingDetails.steps" :key="step.step_number" class="relative bg-white border-l-4 border-blue-400 rounded-lg shadow-md p-3 sm:p-6 mb-8 transition-all duration-300 hover:shadow-xl animate-fade-in">
                <div class="flex items-center mb-4">
                  <span class="inline-flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full mr-3">
                    <svg v-if="step.step_number === 1" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A13.937 13.937 0 0112 15c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                    <svg v-else-if="step.step_number === 2" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 01.88 7.903A4.001 4.001 0 0112 21a4.001 4.001 0 01-4.88-6.097A4 4 0 018 7m8 0V5a4 4 0 00-8 0v2" /></svg>
                    <svg v-else-if="step.step_number === 3" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3-1.343-3-3-3zm0 0V4m0 7v7" /></svg>
                    <svg v-else-if="step.step_number === 4" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4a1 1 0 011-1h8a1 1 0 011 1v12m-4 4h-4a1 1 0 01-1-1v-1h6v1a1 1 0 01-1 1z" /></svg>
                    <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" /></svg>
                  </span>
                  <h5 class="font-bold text-blue-800 text-base sm:text-xl tracking-tight">Step {{ step.step_number }}: {{ step.step_name }}</h5>
                </div>
                <div v-if="step.step_data && Object.keys(step.step_data).length > 0">
                  <!-- Special handling for Document Upload step -->
                  <template v-if="step.step_name.toLowerCase().includes('document') || step.step_number === 4">
                    <div>
                      <template v-if="step.step_data.documents && Object.values(step.step_data.documents).some(doc => doc)">
                        <div v-for="docType in Object.keys(step.step_data.documents)" :key="docType">
                          <div class="flex items-center mb-3 p-3 bg-gray-50 rounded hover:bg-blue-50 transition-colors border border-gray-100" v-if="step.step_data.documents[docType]">
                            <span class="mr-3">
                              <template v-if="isImage(step.step_data.documents[docType].file_path)">
                                <div v-if="loadingImages[docType]" class="w-12 h-12 flex items-center justify-center bg-gray-100 rounded animate-pulse">Loading...</div>
                                <img v-else-if="imageBlobs[docType]" :src="imageBlobs[docType]" class="w-12 h-12 rounded object-cover border" alt="Document Thumbnail" />
                                <div v-else-if="imageErrors[docType]" class="w-12 h-12 flex items-center justify-center bg-red-100 text-red-600 rounded">Error</div>
                                <div v-else class="w-12 h-12 flex items-center justify-center bg-gray-200 text-gray-600 rounded">No Preview</div>
                              </template>
                              <span v-else-if="step.step_data.documents[docType].file_path && step.step_data.documents[docType].file_path.endsWith('.pdf')" class="w-12 h-12 flex items-center justify-center bg-red-100 text-red-600 rounded">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7v10a2 2 0 002 2h6a2 2 0 002-2V7a2 2 0 00-2-2H9a2 2 0 00-2 2z" />
                                </svg>
                                <span class="ml-1 font-bold">PDF</span>
                              </span>
                              <span v-else class="w-12 h-12 flex items-center justify-center bg-gray-200 text-gray-600 rounded">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7v10a2 2 0 002 2h6a2 2 0 002-2V7a2 2 0 00-2-2H9a2 2 0 00-2 2z" />
                                </svg>
                                <span class="ml-1 font-bold">DOC</span>
                              </span>
                            </span>
                            <div class="flex-1">
                              <div class="font-semibold text-gray-700 flex items-center">
                                {{ step.step_data.documents[docType].document_name || docType }}
                                <span class="ml-2 px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-xs font-medium">{{ step.step_data.documents[docType].document_type }}</span>
                              </div>
                              <div class="text-xs text-gray-500">Uploaded: {{ step.step_data.documents[docType].uploaded_at ? new Date(step.step_data.documents[docType].uploaded_at).toLocaleString() : 'N/A' }}</div>
                              <div v-if="step.step_data.documents[docType].status" class="inline-block mt-1 px-2 py-0.5 rounded text-xs font-semibold"
                                :class="{
                                  'bg-green-100 text-green-700': step.step_data.documents[docType].status === 'uploaded',
                                  'bg-yellow-100 text-yellow-700': step.step_data.documents[docType].status === 'processing',
                                  'bg-red-100 text-red-700': step.step_data.documents[docType].status === 'rejected',
                                  'bg-gray-100 text-gray-700': !['uploaded','processing','rejected'].includes(step.step_data.documents[docType].status)
                                }">
                                {{ step.step_data.documents[docType].status.charAt(0).toUpperCase() + step.step_data.documents[docType].status.slice(1) }}
                              </div>
                            </div>
                            <button @click="downloadDocument(step.step_data.documents[docType])" class="ml-4 px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm font-medium transition-colors">Download</button>
                          </div>
                        </div>
                      </template>
                      <div v-else class="text-gray-400 text-sm">No documents uploaded.</div>
                    </div>
                  </template>
                  <template v-else>
                    <dl class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                      <template v-for="(value, key) in step.step_data" :key="key">
                        <template v-if="key !== 'application_summary'">
                          <dt class="font-semibold text-blue-700 capitalize pro">{{ key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) }}</dt>
                          <dd class="text-gray-900 mb-2">
                            <template v-if="typeof value === 'object' && value !== null && !Array.isArray(value)">
                              <div class="bg-blue-50 rounded p-3 mb-2">
                                <dl class="ml-2 border-l-2 border-blue-200 pl-4">
                                  <template v-for="(subValue, subKey) in value" :key="subKey">
                                    <dt class="font-medium text-blue-600 capitalize sub">{{ subKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) }}</dt>
                                    <dd class="text-blue-900 mb-1">
                                      <template v-if="Array.isArray(subValue)">
                                        <span v-for="item in subValue" :key="item" class="inline-block bg-blue-200 text-blue-800 rounded-full px-2 py-0.5 mr-1 mb-1 text-xs font-semibold">{{ item }}</span>
                                      </template>
                                      <template v-else>
                                        {{ subValue }}
                                      </template>
                                    </dd>
                                  </template>
                                </dl>
                              </div>
                            </template>
                            <template v-else-if="Array.isArray(value)">
                              <span v-for="item in value" :key="item" class="inline-block bg-blue-200 text-blue-800 rounded-full px-2 py-0.5 mr-1 mb-1 text-xs font-semibold">{{ item }}</span>
                            </template>
                            <template v-else>
                              {{ value }}
                            </template>
                          </dd>
                        </template>
                      </template>
                    </dl>
                  </template>
                </div>
                <div v-else class="text-gray-400 text-xs sm:text-sm">No data provided for this step.</div>
              </div>
            </div>
            <div class="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3 mt-6 pt-4 border-t">
              <button @click="closeApplicationModal" class="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
              <button @click="openStatusModal(selectedApplication)" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Update Status</button>
            </div>
          </div>
        </div>
      </div>
      <!-- Status Update Modal -->
      <div v-if="showStatusModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
        <div class="relative mx-auto p-2 sm:p-5 border w-full max-w-xs sm:max-w-md shadow-lg rounded-md bg-white">
          <h3 class="text-base sm:text-lg font-medium text-gray-900 mb-4">Update Application Status</h3>
          <div v-if="allowedTransitions.length > 0">
            <select v-model="statusUpdateForm.status" class="w-full mb-4 rounded-md border-gray-300 text-xs sm:text-sm">
              <option value="" disabled>Select new status</option>
              <option v-for="status in allowedTransitions" :key="status" :value="status">{{ getStatusLabel(status) }}</option>
            </select>
            <textarea v-if="statusRequiresReason" v-model="statusUpdateForm.reason" class="w-full mb-4 rounded-md border-gray-300 text-xs sm:text-sm" placeholder="Reason (required for rejection)"></textarea>
            <button @click="updateStatus" :disabled="!statusUpdateForm.status || (statusRequiresReason && !statusUpdateForm.reason)" class="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">Update Status</button>
          </div>
          <div v-else class="text-gray-500">No status transitions available.</div>
          <button @click="closeStatusModal" class="mt-4 w-full px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="isLoading" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-2 text-xs sm:text-sm text-gray-600">Loading...</p>
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
              <p class="text-xs sm:text-sm font-medium" :class="alertType === 'success' ? 'text-green-800' : 'text-red-800'">
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
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
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

const onboardingApplications = ref([])
const isLoadingApplications = ref(false)
const selectedApplication = ref(null)
const applicationDetails = ref(null)
const showStatusModal = ref(false)
const allowedTransitions = ref([])
const statusUpdateForm = ref({ application: null, status: '', reason: '', notes: '' })
const selectedOnboardingDetails = ref(null)
const imageBlobs = ref({});
const loadingImages = ref({});
const imageErrors = ref({});

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

const loadOnboardingApplications = async () => {
  try {
    isLoadingApplications.value = true
    // Only onboarding applications
    const params = new URLSearchParams({ limit: '50', offset: '0' })
    const response = await api.get(`/status/admin/applications?${params}`)
    // Filter for onboarding only
    onboardingApplications.value = (response.data.applications || []).filter(app => app.loan_type === 'Onboarding')
  } catch (error) {
    showAlert('Failed to load onboarding applications', 'error')
  } finally {
    isLoadingApplications.value = false
  }
}

const viewApplication = async (application) => {
  try {
    console.log('View application clicked:', application)
    selectedApplication.value = application
    // Use correct ID for onboarding applications
    let onboardingId = application.id
    if (application.app && application.loan_type === 'Onboarding') {
      onboardingId = application.app.id
    }
    if (application.loan_type !== 'Onboarding') {
      showAlert('This is not an onboarding application.', 'error')
      return
    }
    // Fetch full onboarding application details (with steps)
    const detailsResponse = await api.get(`/onboarding/applications/${onboardingId}`)
    selectedOnboardingDetails.value = detailsResponse.data
    // Optionally fetch status details for status badge
    const statusResponse = await api.get(`/status/applications/${onboardingId}/status`)
    applicationDetails.value = statusResponse.data
  } catch (error) {
    showAlert('Failed to load application details', 'error')
    selectedOnboardingDetails.value = null
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
    await loadOnboardingApplications()
  } catch (error) {
    showAlert('Failed to update status', 'error')
  }
}

const closeApplicationModal = () => {
  selectedApplication.value = null
  applicationDetails.value = null
  selectedOnboardingDetails.value = null
}

const closeStatusModal = () => {
  showStatusModal.value = false
  statusUpdateForm.value = { application: null, status: '', reason: '', notes: '' }
  allowedTransitions.value = []
}

const getStatusLabel = (status) => {
  const statusMap = {
    'in_progress': 'In Progress',
    'submitted': 'Submitted',
    'under_review': 'Under Review',
    'approved': 'Approved',
    'done': 'Completed',
    'rejected': 'Rejected',
    'cancelled': 'Cancelled'
  }
  return statusMap[status] || status
}

const statusRequiresReason = computed(() => {
  return ['rejected', 'cancelled'].includes(statusUpdateForm.value.status)
})

function isImage(filePath) {
  return /\.(jpg|jpeg|png)$/i.test(filePath);
}

async function fetchDocumentBlob(doc) {
  if (!doc || !doc.file_path) return null;
  const parts = doc.file_path.split('/');
  if (parts.length < 4) return null;
  const url = `/api/v1/onboarding/documents/${parts[1]}/${parts[2]}/${parts.slice(3).join('/')}`;
  const token = localStorage.getItem('token');
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!response.ok) return null;
  return await response.blob();
}

async function loadImageBlob(doc, docType) {
  loadingImages.value[docType] = true;
  imageErrors.value[docType] = false;
  try {
    const blob = await fetchDocumentBlob(doc);
    if (blob) {
      imageBlobs.value[docType] = URL.createObjectURL(blob);
    } else {
      imageErrors.value[docType] = true;
    }
  } catch {
    imageErrors.value[docType] = true;
  } finally {
    loadingImages.value[docType] = false;
  }
}

async function downloadDocument(doc) {
  const blob = await fetchDocumentBlob(doc);
  if (blob) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = doc.document_name || 'document';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }
}

// Watch for modal open and load images
watch(selectedOnboardingDetails, async (details) => {
  if (!details || !details.steps) return;
  for (const step of details.steps) {
    if (step.step_name.toLowerCase().includes('document') || step.step_number === 4) {
      const docs = step.step_data.documents || {};
      for (const docType of Object.keys(docs)) {
        const doc = docs[docType];
        if (doc && isImage(doc.file_path)) {
          await nextTick();
          loadImageBlob(doc, docType);
        }
      }
    }
  }
});

onMounted(async () => {
  if (!authStore.isAuthenticated || !['admin', 'loan_officer', 'risk_officer'].includes(authStore.user?.role)) {
    router.push('/login')
    return
  }
  await loadDashboard()
  await loadOnboardingApplications()
})
</script>

<style scoped>
.btn-secondary {
  @apply inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}
.card {
  @apply bg-white shadow rounded-lg p-6;
}
@keyframes fade-in {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: none; }
}
.animate-fade-in {
  animation: fade-in 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
</style> 