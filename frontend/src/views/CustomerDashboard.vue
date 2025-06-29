<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <!-- Status/Info Alert -->
      <div v-if="statusMessage" :class="statusMessage.class" class="rounded-lg p-4 mb-6 flex items-start">
        <div class="flex-shrink-0 mt-1">
          <svg v-if="statusMessage.type === 'success'" class="h-6 w-6 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>
          <svg v-else-if="statusMessage.type === 'error'" class="h-6 w-6 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>
          <svg v-else-if="statusMessage.type === 'warning'" class="h-6 w-6 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.366-.446.957-.446 1.323 0l6.518 7.95c.329.401.04.951-.462.951H2.201c-.502 0-.791-.55-.462-.95l6.518-7.951zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-2a1 1 0 01-1-1V7a1 1 0 112 0v3a1 1 0 01-1 1z" clip-rule="evenodd" /></svg>
          <svg v-else class="h-6 w-6 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10A8 8 0 11 2 10a8 8 0 0116 0zm-8-4a1 1 0 100 2 1 1 0 000-2zm2 8a1 1 0 01-2 0v-1a1 1 0 012 0v1z" clip-rule="evenodd" /></svg>
        </div>
        <div class="ml-3">
          <p class="text-sm font-medium" :class="statusMessage.textClass">{{ statusMessage.text }}</p>
        </div>
      </div>

      <!-- Welcome Section -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900 mb-2">
              Welcome back, {{ authStore.user?.first_name }}!
            </h2>
            <p class="text-gray-600">Manage your applications and track their progress.</p>
          </div>
          
          <!-- Conditional Buttons -->
          <div class="flex space-x-4">
            <!-- Apply for Loan (only if onboarding complete and eligible) -->
            <button
              v-if="canApplyForLoan"
              @click="startLoanApplication"
              :disabled="isCheckingEligibility"
              class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
              </svg>
              {{ isCheckingEligibility ? 'Checking...' : 'Apply for Loan' }}
            </button>
            
            <!-- Start Onboarding (only if not completed) -->
            <button
              v-if="!hasCompletedOnboarding"
              @click="startOnboarding"
              class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              Complete Onboarding
            </button>

            <!-- Info Button for Ineligible Users -->
            <button
              v-if="hasCompletedOnboarding && !canApplyForLoan && !isCheckingEligibility"
              @click="showEligibilityInfo = true"
              class="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Loan Eligibility
            </button>
          </div>
        </div>

        <!-- Success Message -->
        <div v-if="route.query.submitted" class="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm text-green-700">
                Your loan application has been submitted successfully! We'll review it and get back to you within 2-3 business days.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- Error State -->
      <div v-if="!isLoading && error" class="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Applications Section -->
      <div v-if="!isLoading">
        <!-- Application Lists -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Onboarding Applications -->
          <div
            v-if="!hasCompletedOnboarding"
            class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
          >
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900">Onboarding Status</h3>
              <span v-if="onboardingApplications.length" :class="getStatusBadgeClass(onboardingApplications[0].status)">
                {{ formatStatus(onboardingApplications[0].status) }}
              </span>
            </div>
            
            <div v-if="onboardingApplications.length > 0">
              <div v-for="application in onboardingApplications" :key="application.id" class="border-b border-gray-200 pb-4 mb-4 last:border-b-0 last:pb-0 last:mb-0">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h4 class="text-sm font-medium text-gray-900">{{ application.application_number }}</h4>
                    <p class="text-sm text-gray-500 mt-1">Created {{ formatDate(application.created_at) }}</p>
                    
                    <!-- Progress Bar -->
                    <div class="mt-3">
                      <div class="flex items-center justify-between text-sm mb-1">
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

                    <!-- Current Step -->
                    <div class="mt-3">
                      <p class="text-sm text-gray-600">Current Step:</p>
                      <p class="text-sm font-medium text-gray-900">{{ getStepName(application.current_step) }}</p>
                    </div>
                  </div>
                </div>

                <!-- Action Button -->
                <div class="mt-4">
                  <button
                    @click="continueOnboarding(application)"
                    :disabled="application.status === 'under_review'"
                    :class="[
                      'w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg',
                      application.status === 'under_review' 
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                        : 'text-white bg-blue-600 hover:bg-blue-700'
                    ]"
                  >
                    {{ application.status === 'under_review' ? 'Under Review' : 'Continue' }}
                  </button>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-8">
              <div class="text-gray-400 mb-4">
                <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
              </div>
              <h4 class="text-lg font-medium text-gray-900 mb-2">No Onboarding Application</h4>
              <p class="text-gray-500 mb-4">Complete your onboarding to access loan services</p>
              <button
                @click="startOnboarding"
                class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700"
              >
                Start Onboarding
              </button>
            </div>
          </div>
          
          <!-- Loan Applications -->
          <div
            v-if="hasCompletedOnboarding"
            class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
          >
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900">Loan Applications</h3>
              <button
                v-if="canApplyForLoan"
                @click="startLoanApplication"
                class="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700"
              >
                <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
                New
              </button>
            </div>
            
            <div v-if="loanApplications.length > 0">
              <div v-for="application in loanApplications" :key="application.id" class="border-b border-gray-200 pb-4 mb-4 last:border-b-0 last:pb-0 last:mb-0">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center justify-between">
                      <h4 class="text-sm font-medium text-gray-900">{{ application.application_number }}</h4>
                      <span :class="getLoanStatusBadgeClass(application.status)">
                        {{ loanService.formatStatus(application.status) }}
                      </span>
                    </div>
                    <p class="text-sm text-gray-500 mt-1">{{ loanService.formatLoanType(application.loan_type) }}</p>
                    <p class="text-sm font-medium text-gray-900 mt-1">{{ loanService.formatCurrency(application.requested_amount) }}</p>
                    <p class="text-sm text-gray-500">{{ application.repayment_period_months }} months</p>
                    <p class="text-sm text-gray-500 mt-1">Created {{ formatDate(application.created_at) }}</p>
                  </div>
                </div>

                <!-- Action Buttons -->
                <div class="mt-4 flex space-x-2">
                  <button
                    @click="viewLoanApplication(application)"
                    class="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
                  >
                    View Details
                  </button>
                  <button
                    v-if="application.status === 'in_progress'"
                    @click="continueLoanApplication(application)"
                    class="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Continue
                  </button>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-8">
              <div class="text-gray-400 mb-4">
                <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                </svg>
              </div>
              <h4 class="text-lg font-medium text-gray-900 mb-2">No Loan Applications</h4>
              <p class="text-gray-500 mb-4">Apply for a loan to meet your financial needs</p>
              <button
                v-if="canApplyForLoan"
                @click="startLoanApplication"
                class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700"
              >
                Apply for Loan
              </button>
              <p v-else class="text-sm text-gray-500">Complete onboarding first to apply for loans</p>
            </div>
          </div>
        </div>

        <!-- All Applications Table (if there are many) -->
        <div v-if="allApplications.length > 4" class="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900">All Applications</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="app in allApplications" :key="`${app.type}-${app.id}`" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">{{ app.application_number }}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                          :class="app.type === 'loan' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'">
                      {{ app.type === 'loan' ? 'Loan' : 'Onboarding' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div v-if="app.type === 'loan'" class="text-sm text-gray-900">
                      {{ loanService.formatCurrency(app.requested_amount) }}
                    </div>
                    <div v-else class="text-sm text-gray-500">N/A</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="app.type === 'loan' ? getLoanStatusBadgeClass(app.status) : getStatusBadgeClass(app.status)">
                      {{ app.type === 'loan' ? loanService.formatStatus(app.status) : formatStatus(app.status) }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(app.created_at) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button 
                      @click="app.type === 'loan' ? viewLoanApplication(app) : continueOnboarding(app)"
                      class="text-blue-600 hover:text-blue-900"
                    >
                      {{ app.status === 'in_progress' ? 'Continue' : 'View' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Eligibility Info Modal -->
      <div v-if="showEligibilityInfo" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showEligibilityInfo = false">
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white" @click.stop>
          <div class="mt-3">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-medium text-gray-900">Loan Eligibility Information</h3>
              <button @click="showEligibilityInfo = false" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
            
            <div v-if="loanEligibility">
              <div v-if="!loanEligibility.is_eligible" class="mb-4">
                <h4 class="text-sm font-medium text-red-800 mb-2">Not Currently Eligible</h4>
                <ul class="list-disc list-inside text-sm text-red-700 space-y-1">
                  <li v-for="reason in loanEligibility.eligibility_reasons" :key="reason">{{ reason }}</li>
                </ul>
              </div>
              
              <div v-if="loanEligibility.requirements?.length" class="mb-4">
                <h4 class="text-sm font-medium text-gray-800 mb-2">Requirements:</h4>
                <ul class="list-disc list-inside text-sm text-gray-700 space-y-1">
                  <li v-for="requirement in loanEligibility.requirements" :key="requirement">{{ requirement }}</li>
                </ul>
              </div>
              
              <div v-if="loanEligibility.max_loan_amount" class="mb-4">
                <h4 class="text-sm font-medium text-gray-800 mb-2">Maximum Loan Amount:</h4>
                <p class="text-lg font-semibold text-green-600">{{ loanService.formatCurrency(loanEligibility.max_loan_amount) }}</p>
              </div>
            </div>
            
            <div class="mt-6">
              <button
                @click="showEligibilityInfo = false"
                class="w-full inline-flex justify-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onboardingService } from '@/services/onboarding'
import { loanService } from '@/services/loan'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// Reactive data
const onboardingApplications = ref([])
const loanApplications = ref([])
const loanEligibility = ref(null)
const showEligibilityInfo = ref(false)

// UI state
const isLoading = ref(false)
const isCheckingEligibility = ref(false)
const error = ref('')

// Computed properties
const hasCompletedOnboarding = computed(() => {
  // Use user profile's user_state to determine onboarding
  return authStore.user?.user_state?.toLowerCase() === 'onboarded'
})

const canApplyForLoan = computed(() => {
  // Only allow if onboarded and user_state is onboarded
  return hasCompletedOnboarding.value
})

const allApplications = computed(() => {
  const onboarding = onboardingApplications.value.map(app => ({ ...app, type: 'onboarding' }))
  const loans = loanApplications.value.map(app => ({ ...app, type: 'loan' }))
  return [...onboarding, ...loans].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
})

const statusMessage = computed(() => {
  if (isLoading.value) return null
  if (error.value) {
    return {
      type: 'error',
      class: 'bg-red-50 border border-red-200',
      textClass: 'text-red-800',
      text: error.value
    }
  }
  if (!hasCompletedOnboarding.value) {
    if (onboardingApplications.value.length === 0) {
      return {
        type: 'info',
        class: 'bg-blue-50 border border-blue-200',
        textClass: 'text-blue-800',
        text: 'You have not started onboarding. Complete onboarding to access loan services.'
      }
    }
    const app = onboardingApplications.value[0]
    if (app.status === 'in_progress') {
      return {
        type: 'warning',
        class: 'bg-yellow-50 border border-yellow-200',
        textClass: 'text-yellow-800',
        text: 'Your onboarding is in progress. Continue your application to complete onboarding.'
      }
    }
    if (app.status === 'under_review') {
      return {
        type: 'info',
        class: 'bg-blue-50 border border-blue-200',
        textClass: 'text-blue-800',
        text: 'Your onboarding is under review. Please wait for approval.'
      }
    }
    if (app.status === 'rejected') {
      return {
        type: 'error',
        class: 'bg-red-50 border border-red-200',
        textClass: 'text-red-800',
        text: 'Your onboarding was rejected. Please contact support or re-apply.'
      }
    }
  } else {
    // Onboarded
    if (!canApplyForLoan.value) {
      return {
        type: 'warning',
        class: 'bg-yellow-50 border border-yellow-200',
        textClass: 'text-yellow-800',
        text: 'You are onboarded, but not currently eligible to apply for a loan. See eligibility info for details.'
      }
    }
    return {
      type: 'success',
      class: 'bg-green-50 border border-green-200',
      textClass: 'text-green-800',
      text: 'You are fully onboarded! You can now apply for loans.'
    }
  }
  return null
})

// Methods
const loadApplications = async () => {
  try {
    isLoading.value = true
    error.value = ''
    
    // Load onboarding applications
    const onboardingResponse = await onboardingService.getApplications()
    onboardingApplications.value = onboardingResponse.data || []
    
    // Load loan applications
    try {
      const loanResponse = await loanService.getLoanApplications()
      loanApplications.value = loanResponse.applications || []
    } catch (loanError) {
      // If loan applications fail, continue with onboarding only
      console.warn('Failed to load loan applications:', loanError)
      loanApplications.value = []
    }
    
  } catch (err) {
    console.error('Failed to load applications:', err)
    error.value = 'Failed to load applications. Please try again.'
  } finally {
    isLoading.value = false
  }
}

const checkLoanEligibility = async () => {
  if (!hasCompletedOnboarding.value) return
  
  try {
    isCheckingEligibility.value = true
    loanEligibility.value = await loanService.checkEligibility()
  } catch (err) {
    console.warn('Failed to check loan eligibility:', err)
    loanEligibility.value = { is_eligible: false, eligibility_reasons: ['Unable to check eligibility at this time'] }
  } finally {
    isCheckingEligibility.value = false
  }
}

const startOnboarding = async () => {
  try {
    const response = await onboardingService.createApplication()
    router.push(`/onboarding?app=${response.data.id}`)
  } catch (err) {
    console.error('Failed to create onboarding application:', err)
    error.value = err.response?.data?.detail || 'Failed to create new onboarding application. Please try again.'
  }
}

const startLoanApplication = async () => {
  router.push('/loan-application')
}

const continueOnboarding = (application) => {
  router.push(`/onboarding?app=${application.id}`)
}

const continueLoanApplication = (application) => {
  router.push(`/loan-application?app=${application.id}`)
}

const viewLoanApplication = (application) => {
  router.push(`/loan-application?app=${application.id}`)
}

// Utility functions
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

const getLoanStatusBadgeClass = (status) => {
  const colors = loanService.getStatusColor(status)
  const colorClasses = {
    'blue': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800',
    'yellow': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800',
    'orange': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800',
    'green': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800',
    'red': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800',
    'gray': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800',
    'purple': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800'
  }
  return colorClasses[colors] || colorClasses['gray']
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

// Lifecycle
onMounted(async () => {
  await loadApplications()
  await checkLoanEligibility()
})
</script> 