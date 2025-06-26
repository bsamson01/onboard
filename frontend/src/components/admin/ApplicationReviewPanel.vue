<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation Header -->
    <div class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center space-x-4">
            <button @click="goToAdminDashboard" class="text-gray-500 hover:text-gray-700">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
              </svg>
            </button>
            <h1 class="text-xl font-semibold text-gray-900">Admin Panel</h1>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-500">Welcome, {{ authStore.user?.first_name }}</span>
            <button @click="authStore.logout" class="text-sm text-gray-500 hover:text-gray-700">Logout</button>
          </div>
        </div>
      </div>
    </div>

    <div class="py-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- Header -->
        <div class="mb-8 flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Application Review</h1>
            <p class="mt-2 text-gray-600">Review and manage loan applications</p>
          </div>
          <div class="flex space-x-4">
            <!-- Status Filter -->
            <select v-model="statusFilter" @change="loadApplications" 
                    class="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
              <option value="">All Statuses</option>
              <option value="submitted">Submitted</option>
              <option value="under_review">Under Review</option>
              <option value="approved">Approved</option>
              <option value="awaiting_disbursement">Awaiting Disbursement</option>
              <option value="rejected">Rejected</option>
              <option value="cancelled">Cancelled</option>
              <option value="done">Completed</option>
            </select>
            
            <!-- Assignment Filter -->
            <label class="inline-flex items-center">
              <input type="checkbox" v-model="assignedToMe" @change="loadApplications"
                     class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
              <span class="ml-2 text-sm text-gray-700">Assigned to me</span>
            </label>
          </div>
        </div>

        <!-- Statistics Cards -->
        <div v-if="statistics" class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <div class="h-8 w-8 bg-blue-500 rounded-md flex items-center justify-center">
                    <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                  </div>
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">Total Applications</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ statistics.total_applications }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <div class="h-8 w-8 bg-yellow-500 rounded-md flex items-center justify-center">
                    <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  </div>
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">Pending Review</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ statistics.pending_review }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <div class="h-8 w-8 bg-green-500 rounded-md flex items-center justify-center">
                    <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  </div>
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">Completion Rate</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ statistics.completion_rate.toFixed(1) }}%</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <div class="h-8 w-8 bg-purple-500 rounded-md flex items-center justify-center">
                    <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                    </svg>
                  </div>
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">Avg Processing</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ statistics.processing_time_avg_days.toFixed(1) }} days</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Applications List -->
        <div class="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden">
          <!-- Loading State -->
          <div v-if="isLoading" class="flex justify-center items-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>

          <!-- Applications Table -->
          <div v-else-if="applications.length > 0">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Application
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount & Type
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Submitted
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="app in applications" :key="app.id" class="hover:bg-gray-50">
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
                          :class="getStatusBadgeClass(app.status_display.color)">
                      {{ app.status_display.label }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(app.submitted_at || app.created_at) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button @click="viewApplication(app)" 
                            class="text-blue-600 hover:text-blue-900">
                      View
                    </button>
                    <button @click="openStatusModal(app)" 
                            class="text-green-600 hover:text-green-900">
                      Update Status
                    </button>
                    <button v-if="['under_review', 'approved', 'rejected'].includes(app.status)" 
                            @click="unlockApplication(app)"
                            class="text-orange-600 hover:text-orange-900">
                      Unlock
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Pagination -->
            <div class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
              <div class="flex-1 flex justify-between sm:hidden">
                <button @click="previousPage" :disabled="currentPage <= 1"
                        class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50">
                  Previous
                </button>
                <button @click="nextPage" :disabled="!hasNextPage"
                        class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50">
                  Next
                </button>
              </div>
              <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p class="text-sm text-gray-700">
                    Showing {{ ((currentPage - 1) * pageSize) + 1 }} to {{ Math.min(currentPage * pageSize, totalCount) }} of {{ totalCount }} results
                  </p>
                </div>
                <div>
                  <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button @click="previousPage" :disabled="currentPage <= 1"
                            class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50">
                      Previous
                    </button>
                    <button @click="nextPage" :disabled="!hasNextPage"
                            class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50">
                      Next
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <h3 class="mt-4 text-lg font-medium text-gray-900">No Applications Found</h3>
            <p class="mt-2 text-gray-500">No applications match your current filters.</p>
          </div>
        </div>
      </div>

      <!-- Application Details Modal -->
      <div v-if="selectedApplication" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-10 mx-auto p-5 border w-4xl max-w-4xl shadow-lg rounded-md bg-white">
          <div class="mt-3">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-xl font-medium text-gray-900">
                Application #{{ selectedApplication.application_number }}
              </h3>
              <button @click="closeApplicationModal" class="text-gray-400 hover:text-gray-600">
                <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            
            <div v-if="applicationDetails" class="space-y-6">
              <!-- Application Info -->
              <div class="bg-gray-50 p-4 rounded-lg">
                <h4 class="font-medium text-gray-900 mb-3">Application Information</h4>
                <dl class="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Status</dt>
                    <dd class="mt-1">
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                            :class="getStatusBadgeClass(applicationDetails.status_display.color)">
                        {{ applicationDetails.status_display.label }}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Requested Amount</dt>
                    <dd class="mt-1 text-sm text-gray-900">${{ formatCurrency(selectedApplication.requested_amount) }}</dd>
                  </div>
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Loan Type</dt>
                    <dd class="mt-1 text-sm text-gray-900">{{ selectedApplication.loan_type }}</dd>
                  </div>
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Submitted</dt>
                    <dd class="mt-1 text-sm text-gray-900">{{ formatDate(selectedApplication.submitted_at) }}</dd>
                  </div>
                  <div v-if="applicationDetails.assigned_officer_name">
                    <dt class="text-sm font-medium text-gray-500">Assigned Officer</dt>
                    <dd class="mt-1 text-sm text-gray-900">{{ applicationDetails.assigned_officer_name }}</dd>
                  </div>
                  <div v-if="applicationDetails.decision_made_by_name">
                    <dt class="text-sm font-medium text-gray-500">Decision Made By</dt>
                    <dd class="mt-1 text-sm text-gray-900">{{ applicationDetails.decision_made_by_name }}</dd>
                  </div>
                </dl>
              </div>

              <!-- Timeline -->
              <div v-if="applicationTimeline">
                <h4 class="font-medium text-gray-900 mb-3">Application Timeline</h4>
                <div class="flow-root">
                  <ul role="list" class="-mb-8">
                    <li v-for="(step, stepIdx) in applicationTimeline.timeline" :key="step.status" class="relative">
                      <div v-if="stepIdx !== applicationTimeline.timeline.length - 1" 
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
            </div>
            
            <div class="flex justify-end space-x-3 mt-6 pt-4 border-t">
              <button @click="closeApplicationModal"
                      class="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50">
                Close
              </button>
              <button @click="openStatusModal(selectedApplication)"
                      class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                Update Status
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Status Update Modal -->
      <div v-if="showStatusModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
          <div class="mt-3">
            <h3 class="text-lg font-medium text-gray-900 text-center mb-4">Update Application Status</h3>
            
            <div v-if="statusUpdateForm.application" class="mb-4">
              <p class="text-sm text-gray-600 mb-2">
                Application: <span class="font-medium">{{ statusUpdateForm.application.application_number }}</span>
              </p>
              <p class="text-sm text-gray-600">
                Current Status: 
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                      :class="getStatusBadgeClass(statusUpdateForm.application.status_display.color)">
                  {{ statusUpdateForm.application.status_display.label }}
                </span>
              </p>
            </div>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">New Status</label>
                <select v-model="statusUpdateForm.status" 
                        class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select new status...</option>
                  <option v-for="status in allowedTransitions" :key="status" :value="status">
                    {{ getStatusLabel(status) }}
                  </option>
                </select>
              </div>

              <div v-if="statusRequiresReason">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Reason <span class="text-red-500">*</span>
                </label>
                <textarea
                  v-model="statusUpdateForm.reason"
                  rows="3"
                  class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Please provide a reason for this status change..."
                  required></textarea>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Notes (Optional)</label>
                <textarea
                  v-model="statusUpdateForm.notes"
                  rows="2"
                  class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Additional notes..."></textarea>
              </div>
            </div>

            <div class="flex items-center justify-center space-x-4 mt-6">
              <button @click="closeStatusModal"
                      class="px-4 py-2 bg-white text-gray-500 rounded-md border border-gray-300 hover:bg-gray-50">
                Cancel
              </button>
              <button @click="updateStatus"
                      :disabled="isUpdatingStatus || !statusUpdateForm.status || (statusRequiresReason && !statusUpdateForm.reason?.trim())"
                      class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
                <span v-if="isUpdatingStatus">Updating...</span>
                <span v-else>Update Status</span>
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()

// Reactive data
const isLoading = ref(true)
const applications = ref([])
const statistics = ref(null)
const statusFilter = ref('')
const assignedToMe = ref(false)
const currentPage = ref(1)
const pageSize = ref(50)
const totalCount = ref(0)

// Modals
const selectedApplication = ref(null)
const applicationDetails = ref(null)
const applicationTimeline = ref(null)
const showStatusModal = ref(false)
const allowedTransitions = ref([])
const isUpdatingStatus = ref(false)

// Status update form
const statusUpdateForm = ref({
  application: null,
  status: '',
  reason: '',
  notes: ''
})

// Alerts
const alertMessage = ref('')
const alertType = ref('success')

// Computed properties
const hasNextPage = computed(() => {
  return currentPage.value * pageSize.value < totalCount.value
})

const statusRequiresReason = computed(() => {
  return ['rejected', 'cancelled'].includes(statusUpdateForm.value.status)
})

// Load applications data
const loadApplications = async () => {
  try {
    isLoading.value = true
    
    const params = new URLSearchParams({
      limit: pageSize.value.toString(),
      offset: ((currentPage.value - 1) * pageSize.value).toString()
    })
    
    if (statusFilter.value) {
      params.append('status', statusFilter.value)
    }
    
    if (assignedToMe.value) {
      params.append('assigned_to_me', 'true')
    }
    
    const response = await api.get(`/status/admin/applications?${params}`)
    const data = response.data
    
    applications.value = data.applications
    totalCount.value = data.total_count
  } catch (error) {
    console.error('Error loading applications:', error)
    showAlert('Failed to load applications', 'error')
  } finally {
    isLoading.value = false
  }
}

// Load statistics
const loadStatistics = async () => {
  try {
    const response = await api.get('/status/admin/statistics')
    statistics.value = response.data
  } catch (error) {
    console.error('Error loading statistics:', error)
  }
}

// View application details
const viewApplication = async (application) => {
  try {
    selectedApplication.value = application
    
    const [detailsResponse, timelineResponse] = await Promise.all([
      api.get(`/status/applications/${application.id}/status`),
      api.get(`/status/applications/${application.id}/timeline`)
    ])
    
    applicationDetails.value = detailsResponse.data
    applicationTimeline.value = timelineResponse.data
  } catch (error) {
    console.error('Error loading application details:', error)
    showAlert('Failed to load application details', 'error')
  }
}

// Open status update modal
const openStatusModal = async (application) => {
  try {
    statusUpdateForm.value = {
      application,
      status: '',
      reason: '',
      notes: ''
    }
    
    // Get allowed transitions
    const response = await api.get(`/status/applications/${application.id}/allowed-transitions`)
    allowedTransitions.value = response.data.allowed_transitions
    
    showStatusModal.value = true
    
    // Close application details modal if open
    selectedApplication.value = null
  } catch (error) {
    console.error('Error loading allowed transitions:', error)
    showAlert('Failed to load status options', 'error')
  }
}

// Update application status
const updateStatus = async () => {
  try {
    isUpdatingStatus.value = true
    
    const updateData = {
      status: statusUpdateForm.value.status,
      reason: statusUpdateForm.value.reason || null,
      notes: statusUpdateForm.value.notes || null
    }
    
    await api.post(`/status/applications/${statusUpdateForm.value.application.id}/update-status`, updateData)
    
    showAlert('Application status updated successfully', 'success')
    closeStatusModal()
    
    // Reload applications and statistics
    await Promise.all([loadApplications(), loadStatistics()])
  } catch (error) {
    console.error('Error updating status:', error)
    showAlert(error.response?.data?.detail || 'Failed to update status', 'error')
  } finally {
    isUpdatingStatus.value = false
  }
}

// Unlock application for editing
const unlockApplication = async (application) => {
  try {
    if (!confirm(`Are you sure you want to unlock application #${application.application_number} for editing? This will change the status back to "In Progress" and allow the customer to make changes.`)) {
      return
    }
    
    await api.post(`/admin/applications/${application.id}/unlock`)
    
    showAlert('Application unlocked successfully. The customer can now edit their application.', 'success')
    
    // Reload applications and statistics
    await Promise.all([loadApplications(), loadStatistics()])
  } catch (error) {
    console.error('Error unlocking application:', error)
    showAlert(error.response?.data?.detail || 'Failed to unlock application', 'error')
  }
}

// Modal controls
const closeApplicationModal = () => {
  selectedApplication.value = null
  applicationDetails.value = null
  applicationTimeline.value = null
}

const closeStatusModal = () => {
  showStatusModal.value = false
  statusUpdateForm.value = {
    application: null,
    status: '',
    reason: '',
    notes: ''
  }
  allowedTransitions.value = []
}

// Pagination
const nextPage = () => {
  if (hasNextPage.value) {
    currentPage.value++
    loadApplications()
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    loadApplications()
  }
}

// Utility functions
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

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

// Navigation
const goToAdminDashboard = () => {
  router.push('/admin')
}

// Watch for filter changes
watch([statusFilter, assignedToMe], () => {
  currentPage.value = 1
})

// Lifecycle
onMounted(async () => {
  await Promise.all([loadApplications(), loadStatistics()])
})
</script>