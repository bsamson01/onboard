<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">My Application</h1>
        <p class="mt-2 text-gray-600">Track your loan application progress</p>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>

      <!-- No Application State -->
      <div v-else-if="!applications.active_application && applications.completed_applications.length === 0" 
           class="text-center py-12">
        <div class="bg-white rounded-lg shadow p-8">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          <h3 class="mt-4 text-lg font-medium text-gray-900">No Applications Found</h3>
          <p class="mt-2 text-gray-500">You haven't submitted any loan applications yet.</p>
          <router-link 
            to="/onboarding" 
            class="mt-6 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
            Start New Application
          </router-link>
        </div>
      </div>

      <!-- Active Application -->
      <div v-else-if="applications.active_application" class="space-y-6">
        <!-- Application Header -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">
                Application #{{ applications.active_application.application_number }}
              </h2>
              <div class="flex items-center mt-2 space-x-4">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getStatusBadgeClass(applications.active_application.status_display.color)">
                  {{ applications.active_application.status_display.label }}
                </span>
                <span class="text-sm text-gray-500">
                  ${{ formatCurrency(applications.active_application.requested_amount) }} 
                  {{ applications.active_application.loan_type }}
                </span>
              </div>
            </div>
            <div v-if="applicationDetails?.can_be_cancelled" class="flex space-x-3">
              <button @click="showCancelModal = true"
                      class="inline-flex items-center px-3 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50">
                Cancel Application
              </button>
            </div>
          </div>
        </div>

        <!-- Status Timeline -->
        <div v-if="timeline" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-6">Application Progress</h3>
          
          <div class="flow-root">
            <ul role="list" class="-mb-8">
              <li v-for="(step, stepIdx) in timeline.timeline" :key="step.status" class="relative">
                <div v-if="stepIdx !== timeline.timeline.length - 1" 
                     class="absolute top-4 left-4 -ml-px h-full w-0.5"
                     :class="step.is_completed ? 'bg-green-500' : 'bg-gray-300'"></div>
                
                <div class="relative flex space-x-3">
                  <div>
                    <span class="h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white"
                          :class="{
                            'bg-green-500': step.is_completed && !step.is_current,
                            'bg-blue-500': step.is_current,
                            'bg-gray-300': !step.is_completed && !step.is_current
                          }">
                      <svg v-if="step.is_completed && !step.is_current" 
                           class="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" 
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" 
                              clip-rule="evenodd"/>
                      </svg>
                      <div v-else-if="step.is_current" class="h-2.5 w-2.5 bg-white rounded-full"></div>
                      <div v-else class="h-2.5 w-2.5 bg-gray-400 rounded-full"></div>
                    </span>
                  </div>
                  <div class="min-w-0 flex-1 pt-1.5">
                    <div>
                      <p class="text-sm font-medium text-gray-900">{{ step.status_display.label }}</p>
                      <p class="text-sm text-gray-500">{{ step.status_display.description }}</p>
                      <p v-if="step.timestamp" class="text-xs text-gray-400 mt-1">
                        {{ formatDate(step.timestamp) }}
                      </p>
                    </div>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <!-- Application Details -->
        <div v-if="applicationDetails" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Application Details</h3>
          
          <dl class="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
            <div>
              <dt class="text-sm font-medium text-gray-500">Application Number</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ applicationDetails.application_number }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">Current Status</dt>
              <dd class="mt-1">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getStatusBadgeClass(applicationDetails.status_display.color)">
                  {{ applicationDetails.status_display.label }}
                </span>
              </dd>
            </div>
            <div v-if="applicationDetails.submitted_at">
              <dt class="text-sm font-medium text-gray-500">Submitted</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ formatDate(applicationDetails.submitted_at) }}</dd>
            </div>
            <div v-if="applicationDetails.assigned_officer_name">
              <dt class="text-sm font-medium text-gray-500">Assigned Officer</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ applicationDetails.assigned_officer_name }}</dd>
            </div>
            <div v-if="applicationDetails.rejection_reason" class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Rejection Reason</dt>
              <dd class="mt-1 text-sm text-red-600 bg-red-50 p-3 rounded-md">
                {{ applicationDetails.rejection_reason }}
              </dd>
            </div>
            <div v-if="applicationDetails.cancellation_reason" class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Cancellation Reason</dt>
              <dd class="mt-1 text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                {{ applicationDetails.cancellation_reason }}
              </dd>
            </div>
          </dl>
        </div>

        <!-- Status History -->
        <div v-if="timeline && timeline.history.length > 0" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Status History</h3>
          
          <div class="flow-root">
            <ul role="list" class="-mb-8">
              <li v-for="(entry, entryIdx) in timeline.history" :key="entry.id" class="relative">
                <div v-if="entryIdx !== timeline.history.length - 1" 
                     class="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"></div>
                
                <div class="relative flex space-x-3">
                  <div>
                    <span class="h-8 w-8 rounded-full bg-gray-400 flex items-center justify-center ring-8 ring-white">
                      <svg class="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" 
                              d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" 
                              clip-rule="evenodd"/>
                      </svg>
                    </span>
                  </div>
                  <div class="min-w-0 flex-1 pt-1.5">
                    <div>
                      <p class="text-sm text-gray-500">
                        Status changed 
                        <span v-if="entry.from_status">from {{ getStatusLabel(entry.from_status) }}</span>
                        to <span class="font-medium">{{ getStatusLabel(entry.to_status) }}</span>
                        by {{ entry.changed_by_name }}
                      </p>
                      <p v-if="entry.reason" class="text-sm text-gray-600 mt-1 bg-gray-50 p-2 rounded">
                        <span class="font-medium">Reason:</span> {{ entry.reason }}
                      </p>
                      <p v-if="entry.notes" class="text-sm text-gray-600 mt-1">
                        <span class="font-medium">Notes:</span> {{ entry.notes }}
                      </p>
                      <p class="text-xs text-gray-400 mt-1">{{ formatDate(entry.created_at) }}</p>
                    </div>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Completed Applications -->
      <div v-if="applications.completed_applications.length > 0" class="mt-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Previous Applications</h2>
        
        <div class="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Application
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="app in applications.completed_applications" :key="app.id">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ app.application_number }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  ${{ formatCurrency(app.requested_amount) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="getStatusBadgeClass(app.status_display.color)">
                    {{ app.status_display.label }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(app.submitted_at || app.created_at) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- New Application Button -->
      <div v-if="applications.can_create_new && !applications.active_application" class="mt-8 text-center">
        <router-link 
          to="/onboarding" 
          class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
          </svg>
          Start New Application
        </router-link>
      </div>
    </div>

    <!-- Cancel Application Modal -->
    <div v-if="showCancelModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 text-center">Cancel Application</h3>
          <div class="mt-2 px-7 py-3">
            <p class="text-sm text-gray-500 mb-4">
              Are you sure you want to cancel your application? This action cannot be undone.
            </p>
            <div class="mb-4">
              <label for="cancelReason" class="block text-sm font-medium text-gray-700 mb-2">
                Reason for cancellation <span class="text-red-500">*</span>
              </label>
              <textarea
                id="cancelReason"
                v-model="cancelReason"
                rows="3"
                class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Please provide a reason for cancelling your application..."
                required></textarea>
              <p v-if="cancelReasonError" class="mt-1 text-sm text-red-600">{{ cancelReasonError }}</p>
            </div>
          </div>
          <div class="flex items-center justify-center space-x-4 px-4 py-3">
            <button @click="closeCancelModal"
                    class="px-4 py-2 bg-white text-gray-500 rounded-md border border-gray-300 hover:bg-gray-50">
              Keep Application
            </button>
            <button @click="confirmCancel"
                    :disabled="isCancelling || !cancelReason.trim()"
                    class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed">
              <span v-if="isCancelling">Cancelling...</span>
              <span v-else>Cancel Application</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Success/Error Messages -->
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()

// Reactive data
const isLoading = ref(true)
const applications = ref({})
const applicationDetails = ref(null)
const timeline = ref(null)
const showCancelModal = ref(false)
const cancelReason = ref('')
const cancelReasonError = ref('')
const isCancelling = ref(false)
const alertMessage = ref('')
const alertType = ref('success')

// Load applications data
const loadApplications = async () => {
  try {
    isLoading.value = true
    
    // Get user's applications
    const appsResponse = await api.get('/status/applications/my')
    applications.value = appsResponse.data
    
    // If there's an active application, load details and timeline
    if (applications.value.active_application) {
      const appId = applications.value.active_application.id
      
      const [detailsResponse, timelineResponse] = await Promise.all([
        api.get(`/status/applications/${appId}/status`),
        api.get(`/status/applications/${appId}/timeline`)
      ])
      
      applicationDetails.value = detailsResponse.data
      timeline.value = timelineResponse.data
    }
  } catch (error) {
    console.error('Error loading applications:', error)
    showAlert('Failed to load applications', 'error')
  } finally {
    isLoading.value = false
  }
}

// Cancel application
const confirmCancel = async () => {
  if (!cancelReason.value.trim()) {
    cancelReasonError.value = 'Please provide a reason for cancellation'
    return
  }
  
  if (cancelReason.value.trim().length < 10) {
    cancelReasonError.value = 'Reason must be at least 10 characters long'
    return
  }
  
  try {
    isCancelling.value = true
    cancelReasonError.value = ''
    
    const appId = applications.value.active_application.id
    await api.post(`/status/applications/${appId}/cancel`, {
      reason: cancelReason.value.trim()
    })
    
    showAlert('Application cancelled successfully', 'success')
    closeCancelModal()
    
    // Reload data
    await loadApplications()
  } catch (error) {
    console.error('Error cancelling application:', error)
    showAlert(error.response?.data?.detail || 'Failed to cancel application', 'error')
  } finally {
    isCancelling.value = false
  }
}

// Modal functions
const closeCancelModal = () => {
  showCancelModal.value = false
  cancelReason.value = ''
  cancelReasonError.value = ''
}

// Utility functions
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
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

const getStatusLabel = (status) => {
  const statusMap = {
    'in_progress': 'In Progress',
    'submitted': 'Submitted',
    'under_review': 'Under Review',
    'approved': 'Approved',
    'awaiting_disbursement': 'Awaiting Disbursement',
    'done': 'Completed',
    'rejected': 'Rejected',
    'cancelled': 'Cancelled'
  }
  return statusMap[status] || status
}

const showAlert = (message, type = 'success') => {
  alertMessage.value = message
  alertType.value = type
  setTimeout(() => {
    alertMessage.value = ''
  }, 5000)
}

// Lifecycle
onMounted(() => {
  loadApplications()
})
</script>