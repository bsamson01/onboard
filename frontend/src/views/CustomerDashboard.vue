<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-semibold text-gray-900">Customer Dashboard</h1>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-700">Welcome, {{ authStore.user?.first_name }}!</span>
            <button @click="authStore.logout" class="btn-secondary">Logout</button>
          </div>
        </div>
      </div>
    </header>

    <div class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <!-- Welcome Section -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900 mb-2">
              Welcome back, {{ authStore.user?.first_name }}!
            </h2>
            <p class="text-gray-600">Manage your loan applications and track their progress.</p>
          </div>
          <button
            @click="startNewApplication"
            class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            New Application
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Error</h3>
            <p class="mt-1 text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Applications Section -->
      <div v-else>
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Your Applications</h3>
        
        <!-- Active Applications -->
        <div v-if="activeApplications.length > 0" class="mb-8">
          <h4 class="text-md font-medium text-gray-700 mb-4">Active Applications</h4>
          <div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            <div
              v-for="application in activeApplications"
              :key="application.id"
              class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
            >
              <div class="flex items-start justify-between mb-4">
                <div>
                  <h5 class="text-lg font-semibold text-gray-900">{{ application.application_number }}</h5>
                  <p class="text-sm text-gray-500">Created {{ formatDate(application.created_at) }}</p>
                </div>
                <span :class="getStatusBadgeClass(application.status)">
                  {{ formatStatus(application.status) }}
                </span>
              </div>
              
              <div class="mb-4">
                <div class="flex items-center justify-between text-sm mb-2">
                  <span class="text-gray-600">Progress</span>
                  <span class="font-medium">{{ application.progress_percentage }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-blue-600 h-2 rounded-full"
                    :style="{ width: `${application.progress_percentage}%` }"
                  ></div>
                </div>
              </div>

              <div class="mb-4">
                <p class="text-sm text-gray-600 mb-2">Current Step:</p>
                <p class="text-sm font-medium text-gray-900">{{ getStepName(application.current_step) }}</p>
              </div>

              <!-- Note for applications under review -->
              <div v-if="application.status === 'under_review'" class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div class="flex">
                  <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                  </div>
                  <div class="ml-3">
                    <p class="text-sm text-yellow-800">
                      <strong>Application Under Review:</strong> Your application is currently being reviewed by our team. 
                      If you need to make changes, please contact support.
                    </p>
                  </div>
                </div>
              </div>

              <button
                @click="continueApplication(application)"
                :disabled="application.status === 'under_review'"
                :class="[
                  'w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg',
                  application.status === 'under_review' 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                    : 'text-white bg-blue-600 hover:bg-blue-700'
                ]"
              >
                {{ application.status === 'under_review' ? 'Under Review' : 'Continue Application' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Completed Applications -->
        <div v-if="completedApplications.length > 0" class="mb-8">
          <h4 class="text-md font-medium text-gray-700 mb-4">Completed Applications</h4>
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Submitted</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Credit Score</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="application in completedApplications" :key="application.id">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div class="text-sm font-medium text-gray-900">{{ application.application_number }}</div>
                        <div class="text-sm text-gray-500">{{ formatDate(application.created_at) }}</div>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span :class="getStatusBadgeClass(application.status)">
                        {{ formatStatus(application.status) }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ application.submitted_at ? formatDate(application.submitted_at) : 'N/A' }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div v-if="application.eligibility_result" class="flex items-center">
                        <span class="text-sm font-medium" :class="getCreditScoreColor(application.eligibility_result.score)">
                          {{ application.eligibility_result.score }}
                        </span>
                        <span class="ml-2 text-xs text-gray-500">({{ application.eligibility_result.grade }})</span>
                      </div>
                      <span v-else class="text-sm text-gray-500">N/A</span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button @click="viewApplicationDetails(application)" class="text-blue-600 hover:text-blue-900 mr-4">View Details</button>
                      <button @click="downloadApplication(application)" class="text-gray-600 hover:text-gray-900">Download</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- No Applications -->
        <div v-if="applications.length === 0" class="text-center py-12">
          <h3 class="text-lg font-medium text-gray-900 mb-2">No applications yet</h3>
          <p class="text-gray-500 mb-6">Start your first loan application to get access to microfinance solutions.</p>
          <button
            @click="startNewApplication"
            class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700"
          >
            Start Application
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onboardingService } from '@/services/onboarding'

const router = useRouter()
const authStore = useAuthStore()

const applications = ref([])
const isLoading = ref(false)
const error = ref('')

const activeApplications = computed(() => {
  return applications.value.filter(app => 
    ['draft', 'in_progress', 'pending_documents', 'under_review'].includes(app.status)
  )
})

const completedApplications = computed(() => {
  return applications.value.filter(app => 
    ['approved', 'rejected', 'completed'].includes(app.status)
  )
})

const loadApplications = async () => {
  try {
    isLoading.value = true
    error.value = ''
    const response = await onboardingService.getApplications()
    applications.value = response.data
  } catch (err) {
    console.error('Failed to load applications:', err)
    error.value = 'Failed to load applications. Please try again.'
  } finally {
    isLoading.value = false
  }
}

const startNewApplication = async () => {
  try {
    const response = await onboardingService.createApplication()
    router.push(`/onboarding?app=${response.data.id}`)
  } catch (err) {
    console.error('Failed to create application:', err)
    error.value = 'Failed to create new application. Please try again.'
  }
}

const continueApplication = (application) => {
  router.push(`/onboarding?app=${application.id}`)
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatStatus = (status) => {
  const statusMap = {
    'draft': 'Draft',
    'in_progress': 'In Progress',
    'pending_documents': 'Pending Documents',
    'under_review': 'Under Review',
    'approved': 'Approved',
    'rejected': 'Rejected',
    'completed': 'Completed'
  }
  return statusMap[status] || status
}

const getStatusBadgeClass = (status) => {
  const classes = {
    'draft': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800',
    'in_progress': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800',
    'pending_documents': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800',
    'under_review': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800',
    'approved': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800',
    'rejected': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800',
    'completed': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800'
  }
  return classes[status] || classes['draft']
}

const getStepName = (stepNumber) => {
  const steps = {
    1: 'Personal Information',
    2: 'Contact Information',
    3: 'Financial Profile',
    4: 'Document Upload',
    5: 'Review & Scoring'
  }
  return steps[stepNumber] || 'Unknown Step'
}

const getCreditScoreColor = (score) => {
  if (score >= 750) return 'text-green-600'
  if (score >= 700) return 'text-blue-600'
  if (score >= 650) return 'text-yellow-600'
  return 'text-red-600'
}

const viewApplicationDetails = (application) => {
  router.push(`/onboarding?app=${application.id}`)
}

const downloadApplication = (application) => {
  const summary = `
Application Summary
==================
Application Number: ${application.application_number}
Status: ${formatStatus(application.status)}
Created: ${formatDate(application.created_at)}
Submitted: ${application.submitted_at ? formatDate(application.submitted_at) : 'N/A'}

Credit Score: ${application.eligibility_result?.score || 'N/A'}
Grade: ${application.eligibility_result?.grade || 'N/A'}

Progress: ${application.progress_percentage}%
Current Step: ${getStepName(application.current_step)}
  `.trim()

  const blob = new Blob([summary], { type: 'text/plain' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `application-${application.application_number}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

onMounted(() => {
  loadApplications()
})
</script> 