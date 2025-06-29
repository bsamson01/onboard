<template>
  <div class="space-y-8">
    <div class="text-center">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">Consent & Authorization</h2>
      <p class="text-lg text-gray-600">Please review and provide consent for credit scoring and data processing</p>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-8">
      <!-- Consent Section -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          Consent & Authorization
        </h3>
        
        <div class="space-y-6">
          <div class="space-y-4">
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0 mt-1">
                <input
                  id="credit_check_consent"
                  v-model="consent.consent_credit_check"
                  type="checkbox"
                  required
                  class="h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 transition-all duration-200"
                />
              </div>
              <div class="flex-1">
                <label for="credit_check_consent" class="block text-sm font-semibold text-gray-900 mb-2">
                  Credit Check Authorization *
                </label>
                <p class="text-sm text-gray-600 leading-relaxed">
                  I authorize the microfinance institution to perform credit checks and obtain my credit report from credit bureaus. 
                  This authorization is valid for the duration of my loan application and any subsequent loan relationships.
                </p>
              </div>
            </div>
          </div>

          <div class="flex items-start space-x-3">
            <div class="flex-shrink-0 mt-1">
              <input
                id="data_processing_consent"
                v-model="consent.consent_data_processing"
                type="checkbox"
                required
                class="h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 transition-all duration-200"
              />
            </div>
            <div class="flex-1">
              <label for="data_processing_consent" class="block text-sm font-semibold text-gray-900 mb-2">
                Data Processing Consent *
              </label>
              <p class="text-sm text-gray-600 leading-relaxed">
                I consent to the processing of my personal data for loan assessment, risk evaluation, and regulatory compliance purposes. 
                I understand that my data will be handled in accordance with applicable privacy laws and regulations.
              </p>
            </div>
          </div>

          <div class="flex items-start space-x-3">
            <div class="flex-shrink-0 mt-1">
              <input
                id="terms_acceptance"
                v-model="consent.terms_acceptance"
                type="checkbox"
                required
                class="h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 transition-all duration-200"
              />
            </div>
            <div class="flex-1">
              <label for="terms_acceptance" class="block text-sm font-semibold text-gray-900 mb-2">
                Terms and Conditions Acceptance *
              </label>
              <p class="text-sm text-gray-600 leading-relaxed">
                I have read, understood, and agree to the terms and conditions of the loan application process, 
                including all applicable fees, interest rates, and repayment terms.
              </p>
            </div>
          </div>

          <div class="flex items-start space-x-3">
            <div class="flex-shrink-0 mt-1">
              <input
                id="marketing_consent"
                v-model="consent.consent_marketing"
                type="checkbox"
                class="h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 transition-all duration-200"
              />
            </div>
            <div class="flex-1">
              <label for="marketing_consent" class="block text-sm font-semibold text-gray-900 mb-2">
                Marketing Communications (Optional)
              </label>
              <p class="text-sm text-gray-600 leading-relaxed">
                I consent to receive marketing communications about financial products and services. 
                I understand I can withdraw this consent at any time by contacting the institution.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation Buttons -->
      <div class="flex justify-between pt-8">
        <button
          type="button"
          @click="$emit('previous')"
          class="px-6 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200"
        >
          <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
          </svg>
          Previous
        </button>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="px-6 py-3 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          <span v-if="isSubmitting" class="flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Saving...
          </span>
          <span v-else class="flex items-center">
            Next
            <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

const props = defineProps({
  application: {
    type: Object,
    default: null
  },
  stepData: {
    type: Object,
    default: () => ({})
  },
  isReadOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['next', 'previous', 'update-data'])

const isSubmitting = ref(false)
const errors = reactive({})

const consent = reactive({
  consent_credit_check: false,
  consent_data_processing: false,
  terms_acceptance: false,
  consent_marketing: false
})

const applicationSummary = reactive({
  personal: {},
  contact: {},
  financial: {},
  documents: {}
})

const hasAllRequiredConsent = computed(() => {
  return consent.consent_credit_check && consent.consent_data_processing && consent.terms_acceptance
})

const validateForm = () => {
  errors.value = {}
  
  if (!consent.consent_credit_check) {
    errors.consent = 'Credit check consent is required'
    return false
  }
  
  if (!consent.consent_data_processing) {
    errors.consent = 'Data processing consent is required'
    return false
  }
  
  if (!consent.terms_acceptance) {
    errors.consent = 'Terms and conditions acceptance is required'
    return false
  }
  
  return true
}

const handleSubmit = async () => {
  if (isReadOnly) {
    // In read-only mode, just navigate to next step without validation or submission
    const submissionData = {
      ...consent,  // Send consent fields at top level
      application_summary: { ...applicationSummary }
    }
    emit('next', submissionData)
    return
  }
  
  if (!validateForm()) {
    return
  }
  
  isSubmitting.value = true
  
  try {
    const submissionData = {
      ...consent,  // Send consent fields at top level
      application_summary: { ...applicationSummary }
    }
    
    emit('next', submissionData)
  } catch (error) {
    console.error('Error submitting application:', error)
  } finally {
    isSubmitting.value = false
  }
}

onMounted(async () => {
  // Load existing data if available
  if (props.stepData && Object.keys(props.stepData).length > 0) {
    const data = { ...props.stepData }
    
    // Handle consent fields
    if (data.consent) {
      Object.assign(consent, data.consent)
    } else {
      // Handle consent fields at top level
      if (data.consent_credit_check !== undefined) {
        consent.consent_credit_check = data.consent_credit_check
      }
      if (data.consent_data_processing !== undefined) {
        consent.consent_data_processing = data.consent_data_processing
      }
      if (data.terms_acceptance !== undefined) {
        consent.terms_acceptance = data.terms_acceptance
      }
      if (data.consent_marketing !== undefined) {
        consent.consent_marketing = data.consent_marketing
      }
    }
    
    // Handle other fields
    if (data.application_summary) {
      Object.assign(applicationSummary, data.application_summary)
    }
  }
  
  // Load application summary from previous steps
  if (props.application && props.application.steps) {
    // Load data from completed steps
    props.application.steps.forEach(step => {
      if (step.is_completed && step.step_data) {
        switch (step.step_number) {
          case 1: // Personal Info
            applicationSummary.personal = { ...step.step_data }
            break
          case 2: // Contact Info
            applicationSummary.contact = { ...step.step_data }
            break
          case 3: // Financial Profile
            applicationSummary.financial = { ...step.step_data }
            break
          case 4: // Documents
            applicationSummary.documents = { ...step.step_data }
            break
        }
      }
    })
  }
})
</script> 