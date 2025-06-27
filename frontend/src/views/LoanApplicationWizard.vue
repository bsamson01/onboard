<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Loan Application</h1>
            <p class="mt-2 text-gray-600">Apply for a loan to meet your financial needs</p>
          </div>
          <div class="text-right">
            <div class="text-sm text-gray-500">Application ID</div>
            <div class="text-lg font-mono text-gray-900">{{ application?.application_number || 'New' }}</div>
          </div>
        </div>
      </div>

      <!-- Eligibility Check -->
      <div v-if="!isEligible && !isLoadingEligibility" class="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Not Eligible for Loan Application</h3>
            <div class="mt-2 text-sm text-red-700">
              <ul class="list-disc list-inside space-y-1">
                <li v-for="reason in eligibilityInfo?.eligibility_reasons" :key="reason">{{ reason }}</li>
              </ul>
            </div>
            <div v-if="eligibilityInfo?.requirements?.length" class="mt-4">
              <h4 class="text-sm font-medium text-red-800">Requirements:</h4>
              <ul class="list-disc list-inside space-y-1 text-sm text-red-700 mt-1">
                <li v-for="requirement in eligibilityInfo.requirements" :key="requirement">{{ requirement }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Loan Application Form -->
      <div v-if="isEligible" class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <!-- Form Header -->
        <div class="mb-8">
          <h2 class="text-2xl font-bold text-gray-900 mb-2">Loan Application Details</h2>
          <p class="text-gray-600">Please provide the details for your loan application</p>
        </div>

        <!-- Read-only Notice -->
        <div v-if="isReadOnly" class="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5" :class="`text-${statusInfo?.color}-400`" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium" :class="`text-${statusInfo?.color}-800`">
                Application {{ statusInfo?.label }}
              </h3>
              <div class="mt-2 text-sm" :class="`text-${statusInfo?.color}-700`">
                <p>{{ statusInfo?.message }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Error Display -->
        <div v-if="error" class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
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

        <!-- Validation Errors -->
        <div v-if="validationErrors.length" class="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-yellow-800">Please fix the following errors:</h3>
              <ul class="mt-2 list-disc list-inside text-sm text-yellow-700">
                <li v-for="error in validationErrors" :key="error">{{ error }}</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Form -->
        <form @submit.prevent="isReadOnly ? null : handleSubmit" class="space-y-8">
          <!-- Loan Type -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-4">Loan Type</label>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div 
                v-for="loanType in loanTypeOptions" 
                :key="loanType.value"
                @click="!isReadOnly && (formData.loan_type = loanType.value)"
                :class="[
                  'relative rounded-lg border p-4 transition-colors',
                  formData.loan_type === loanType.value 
                    ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-500' 
                    : 'border-gray-300 hover:border-gray-400',
                  isReadOnly ? 'cursor-default' : 'cursor-pointer'
                ]"
              >
                <div class="flex items-center">
                  <input
                    type="radio"
                    :value="loanType.value"
                    v-model="formData.loan_type"
                    :disabled="isReadOnly"
                    class="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 disabled:opacity-50"
                  >
                  <div class="ml-3">
                    <label class="block text-sm font-medium text-gray-900" :class="{ 'cursor-pointer': !isReadOnly, 'cursor-default': isReadOnly }">
                      {{ loanType.label }}
                    </label>
                    <p class="text-sm text-gray-500">{{ loanType.description }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Requested Amount -->
          <div>
            <label for="requested_amount" class="block text-sm font-medium text-gray-700 mb-2">
              Requested Amount *
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span class="text-gray-500 text-lg">$</span>
              </div>
              <input
                type="number"
                id="requested_amount"
                v-model.number="formData.requested_amount"
                :max="eligibilityInfo?.max_loan_amount || 1000000"
                min="1"
                step="1"
                :disabled="isReadOnly"
                class="block w-full pl-8 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-lg disabled:opacity-50 disabled:bg-gray-50"
                placeholder="10000"
              >
            </div>
            <p v-if="eligibilityInfo?.max_loan_amount" class="mt-1 text-sm text-gray-500">
              Maximum eligible amount: {{ loanService.formatCurrency(eligibilityInfo.max_loan_amount) }}
            </p>
            <p v-if="formData.requested_amount && estimatedMonthlyPayment" class="mt-1 text-sm text-blue-600">
              Estimated monthly payment: {{ loanService.formatCurrency(estimatedMonthlyPayment) }}
            </p>
          </div>

          <!-- Repayment Period -->
          <div>
            <label for="repayment_period" class="block text-sm font-medium text-gray-700 mb-2">
              Repayment Period *
            </label>
            <select
              id="repayment_period"
              v-model.number="formData.repayment_period_months"
              :disabled="isReadOnly"
              class="block w-full py-3 px-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50"
            >
              <option value="">Select repayment period</option>
              <option 
                v-for="term in repaymentTermOptions" 
                :key="term.value" 
                :value="term.value"
              >
                {{ term.label }} - {{ term.description }}
              </option>
            </select>
          </div>

          <!-- Loan Purpose -->
          <div>
            <label for="loan_purpose" class="block text-sm font-medium text-gray-700 mb-2">
              Loan Purpose *
            </label>
            <textarea
              id="loan_purpose"
              v-model="formData.loan_purpose"
              rows="4"
              :disabled="isReadOnly"
              class="block w-full py-3 px-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50"
              placeholder="Please describe how you plan to use this loan (minimum 10 characters)"
            ></textarea>
            <p class="mt-1 text-sm text-gray-500">
              {{ formData.loan_purpose?.length || 0 }} / 500 characters (minimum 10 required)
            </p>
          </div>

          <!-- Additional Notes -->
          <div>
            <label for="additional_notes" class="block text-sm font-medium text-gray-700 mb-2">
              Additional Notes (Optional)
            </label>
            <textarea
              id="additional_notes"
              v-model="formData.additional_notes"
              rows="3"
              :disabled="isReadOnly"
              class="block w-full py-3 px-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50"
              placeholder="Any additional information you'd like to provide"
            ></textarea>
            <p class="mt-1 text-sm text-gray-500">
              {{ formData.additional_notes?.length || 0 }} / 1000 characters
            </p>
          </div>

          <!-- Form Actions -->
          <div class="flex items-center justify-between pt-6 border-t border-gray-200">
            <button
              type="button"
              @click="goBack"
              class="inline-flex items-center px-6 py-3 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
              </svg>
              Back to Dashboard
            </button>

            <!-- Status indicator for read-only applications -->
            <div v-if="isReadOnly" class="flex items-center">
              <div class="flex items-center px-4 py-2 rounded-lg" :class="{
                'bg-green-50 text-green-800 border border-green-200': application?.status === 'approved',
                'bg-red-50 text-red-800 border border-red-200': application?.status === 'rejected',
                'bg-blue-50 text-blue-800 border border-blue-200': application?.status === 'submitted'
              }">
                <svg v-if="application?.status === 'approved'" class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                <svg v-else-if="application?.status === 'rejected'" class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
                <svg v-else class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
                </svg>
                <span class="text-sm font-medium capitalize">{{ application?.status?.replace('_', ' ') }}</span>
              </div>
            </div>

            <!-- Action buttons for editable applications -->
            <div v-else class="flex space-x-4">
              <button
                v-if="application && application.status === 'in_progress'"
                type="button"
                @click="saveDraft"
                :disabled="isSaving"
                class="inline-flex items-center px-6 py-3 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <svg v-if="isSaving" class="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-700" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ isSaving ? 'Saving...' : 'Save Draft' }}
              </button>

              <button
                type="submit"
                :disabled="isSubmitting || validationErrors.length > 0"
                class="inline-flex items-center px-8 py-3 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg v-if="isSubmitting" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ application ? 'Submit Application' : 'Create Application' }}
              </button>
            </div>
          </div>
        </form>
      </div>

      <!-- Loading State -->
      <div v-if="isLoadingEligibility" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { loanService } from '@/services/loan'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// Reactive data
const application = ref(null)
const eligibilityInfo = ref(null)
const formData = ref({
  loan_type: '',
  requested_amount: null,
  repayment_period_months: null,
  loan_purpose: '',
  additional_notes: ''
})

// UI state
const isLoadingEligibility = ref(true)
const isSubmitting = ref(false)
const isSaving = ref(false)
const error = ref('')
const validationErrors = ref([])

// Options
const loanTypeOptions = loanService.getLoanTypeOptions()
const repaymentTermOptions = loanService.getRepaymentTermOptions()

// Loan status info
const loanStatusInfo = {
  in_progress: {
    label: 'In Progress',
    color: 'blue',
    message: 'You can continue editing your application.'
  },
  submitted: {
    label: 'Submitted',
    color: 'yellow',
    message: 'Your loan application has been submitted and is currently under review. You cannot make changes to the application at this time.'
  },
  under_review: {
    label: 'Under Review',
    color: 'orange',
    message: 'Your application is under review. Please wait for a decision.'
  },
  approved: {
    label: 'Approved',
    color: 'green',
    message: 'Your application has been approved! Please check your email for further instructions.'
  },
  rejected: {
    label: 'Rejected',
    color: 'red',
    message: 'Your application has been reviewed and was not approved. Please contact our support team if you have any questions.'
  },
  cancelled: {
    label: 'Cancelled',
    color: 'gray',
    message: 'This application was cancelled and cannot be edited.'
  },
  awaiting_disbursement: {
    label: 'Awaiting Disbursement',
    color: 'purple',
    message: 'Your application is approved and awaiting disbursement.'
  },
  done: {
    label: 'Completed',
    color: 'green',
    message: 'Your loan application process is complete.'
  },
  completed: {
    label: 'Completed',
    color: 'green',
    message: 'Your loan application process is complete.'
  }
}

const statusInfo = computed(() => {
  if (!application.value?.status) return null
  return loanStatusInfo[application.value.status] || {
    label: application.value.status,
    color: 'gray',
    message: 'Status unknown.'
  }
})

// Computed properties
const isEligible = computed(() => {
  return eligibilityInfo.value?.is_eligible === true
})

const isReadOnly = computed(() => {
  return !['in_progress', 'draft'].includes(application.value?.status)
})

const canEdit = computed(() => {
  return !isReadOnly.value && (application.value?.status === 'in_progress' || !application.value)
})

const estimatedMonthlyPayment = computed(() => {
  if (!formData.value.requested_amount || !formData.value.repayment_period_months) {
    return null
  }
  
  // Use a default interest rate for estimation (this would come from the backend in real scenario)
  const estimatedRate = 12 // 12% annual rate
  return loanService.calculateMonthlyPayment(
    formData.value.requested_amount,
    estimatedRate,
    formData.value.repayment_period_months
  )
})

// Watch for form changes to validate
watch(formData, () => {
  validateForm()
}, { deep: true })

// Methods
const checkEligibility = async () => {
  try {
    isLoadingEligibility.value = true
    // Pass application id if editing
    const appId = route.query.app || (application.value && application.value.id)
    eligibilityInfo.value = await loanService.checkEligibility(appId)
  } catch (err) {
    console.error('Eligibility check failed:', err)
    error.value = loanService.handleApiError(err)
  } finally {
    isLoadingEligibility.value = false
  }
}

const validateForm = () => {
  validationErrors.value = loanService.validateLoanApplication(formData.value)
}

const loadExistingApplication = async () => {
  const applicationId = route.query.app
  if (applicationId) {
    try {
      application.value = await loanService.getLoanApplication(applicationId)
      // Populate form with existing data
      formData.value = {
        loan_type: application.value.loan_type,
        requested_amount: application.value.requested_amount,
        repayment_period_months: application.value.repayment_period_months,
        loan_purpose: application.value.loan_purpose,
        additional_notes: application.value.internal_notes?.customer_notes || ''
      }
      // Re-check eligibility with app id after loading
      await checkEligibility()
    } catch (err) {
      console.error('Failed to load application:', err)
      error.value = loanService.handleApiError(err)
    }
  }
}

const saveDraft = async () => {
  try {
    isSaving.value = true
    error.value = ''
    
    if (application.value) {
      // Update existing application
      await loanService.updateLoanApplication(application.value.id, formData.value)
    } else {
      // This shouldn't happen in normal flow, but handle it
      const newApplication = await loanService.createLoanApplication(formData.value)
      application.value = newApplication
      // Update URL to include application ID
      router.replace({ query: { ...route.query, app: newApplication.id } })
    }
    
    // Show success message briefly
    const originalError = error.value
    error.value = ''
    setTimeout(() => {
      if (!error.value) error.value = originalError
    }, 2000)
    
  } catch (err) {
    console.error('Failed to save draft:', err)
    error.value = loanService.handleApiError(err)
  } finally {
    isSaving.value = false
  }
}

const handleSubmit = async () => {
  // Prevent submission if form is read-only
  if (isReadOnly.value) {
    return
  }
  
  try {
    isSubmitting.value = true
    error.value = ''
    
    // Validate form
    validateForm()
    if (validationErrors.value.length > 0) {
      return
    }
    
    let targetApplication
    
    if (application.value) {
      // Update and submit existing application
      targetApplication = await loanService.updateLoanApplication(application.value.id, formData.value)
      await loanService.submitLoanApplication(targetApplication.id)
    } else {
      // Create new application and submit
      targetApplication = await loanService.createLoanApplication(formData.value)
      await loanService.submitLoanApplication(targetApplication.id)
    }
    
    // Redirect to success page or dashboard
    router.push({
      name: 'CustomerDashboard',
      query: { submitted: targetApplication.id }
    })
    
  } catch (err) {
    console.error('Failed to submit application:', err)
    error.value = loanService.handleApiError(err)
  } finally {
    isSubmitting.value = false
  }
}

const goBack = () => {
  router.push({ name: 'CustomerDashboard' })
}

// Lifecycle
onMounted(async () => {
  // If editing, load app first, then check eligibility with app id
  if (route.query.app) {
    await loadExistingApplication()
  } else {
    await checkEligibility()
  }
})
</script>