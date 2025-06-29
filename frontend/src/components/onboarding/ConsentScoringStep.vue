<template>
  <div class="space-y-8">
    <div class="text-center">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">Consent & Credit Scoring</h2>
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

      <!-- Credit Scoring Preferences -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
          Credit Scoring Preferences
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label for="credit_score_range" class="block text-sm font-semibold text-gray-700">Credit Score Range</label>
            <select
              id="credit_score_range"
              v-model="formData.credit_score_range"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.credit_score_range }"
            >
              <option value="">Select credit score range</option>
              <option value="excellent">Excellent (750-850)</option>
              <option value="good">Good (700-749)</option>
              <option value="fair">Fair (650-699)</option>
              <option value="poor">Poor (300-649)</option>
              <option value="unknown">Unknown</option>
            </select>
            <p v-if="errors.credit_score_range" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.credit_score_range }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="risk_tolerance" class="block text-sm font-semibold text-gray-700">Risk Tolerance Level</label>
            <select
              id="risk_tolerance"
              v-model="formData.risk_tolerance"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.risk_tolerance }"
            >
              <option value="">Select risk tolerance</option>
              <option value="conservative">Conservative</option>
              <option value="moderate">Moderate</option>
              <option value="aggressive">Aggressive</option>
            </select>
            <p v-if="errors.risk_tolerance" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.risk_tolerance }}
            </p>
          </div>
        </div>
      </div>

      <!-- Additional Information -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
          </svg>
          Additional Information
        </h3>
        
        <div class="space-y-6">
          <div class="space-y-2">
            <label for="loan_purpose" class="block text-sm font-semibold text-gray-700">Primary Loan Purpose *</label>
            <select
              id="loan_purpose"
              v-model="formData.loan_purpose"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.loan_purpose }"
            >
              <option value="">Select loan purpose</option>
              <option value="business">Business/Entrepreneurship</option>
              <option value="education">Education</option>
              <option value="home_improvement">Home Improvement</option>
              <option value="debt_consolidation">Debt Consolidation</option>
              <option value="emergency">Emergency Expenses</option>
              <option value="vehicle">Vehicle Purchase</option>
              <option value="wedding">Wedding</option>
              <option value="medical">Medical Expenses</option>
              <option value="other">Other</option>
            </select>
            <p v-if="errors.loan_purpose" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.loan_purpose }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="loan_amount" class="block text-sm font-semibold text-gray-700">Requested Loan Amount *</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <span class="text-gray-500 text-lg font-medium">$</span>
              </div>
              <input
                id="loan_amount"
                v-model.number="formData.loan_amount"
                type="number"
                min="100"
                step="100"
                required
                class="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
                :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.loan_amount }"
                placeholder="0.00"
              />
            </div>
            <p v-if="errors.loan_amount" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.loan_amount }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="loan_term_months" class="block text-sm font-semibold text-gray-700">Preferred Loan Term *</label>
            <select
              id="loan_term_months"
              v-model="formData.loan_term_months"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.loan_term_months }"
            >
              <option value="">Select loan term</option>
              <option value="6">6 months</option>
              <option value="12">12 months</option>
              <option value="18">18 months</option>
              <option value="24">24 months</option>
              <option value="36">36 months</option>
              <option value="48">48 months</option>
              <option value="60">60 months</option>
            </select>
            <p v-if="errors.loan_term_months" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.loan_term_months }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="additional_notes" class="block text-sm font-semibold text-gray-700">Additional Notes</label>
            <textarea
              id="additional_notes"
              v-model="formData.additional_notes"
              rows="4"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400 resize-none"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.additional_notes }"
              placeholder="Please provide any additional information that may be relevant to your loan application..."
            ></textarea>
            <p v-if="errors.additional_notes" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.additional_notes }}
            </p>
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
const isCalculatingScore = ref(false)
const errors = reactive({})
const creditScore = ref(null)

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

const formData = reactive({
  loan_amount: null,
  loan_term_months: '',
  additional_notes: '',
  credit_score_range: '',
  risk_tolerance: '',
  loan_purpose: ''
})

const hasAllRequiredConsent = computed(() => {
  return consent.consent_credit_check && consent.consent_data_processing && consent.terms_acceptance
})

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

const formatCurrency = (amount) => {
  if (!amount) return '0.00'
  return parseFloat(amount).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const getCreditScoreColor = (score) => {
  if (score >= 750) return 'text-green-600'
  if (score >= 700) return 'text-blue-600'
  if (score >= 650) return 'text-yellow-600'
  return 'text-red-600'
}

const getRiskLevelClass = (riskLevel) => {
  const classes = {
    'Low': 'bg-green-100 text-green-800',
    'Medium': 'bg-yellow-100 text-yellow-800',
    'High': 'bg-red-100 text-red-800'
  }
  return classes[riskLevel] || 'bg-gray-100 text-gray-800'
}

const calculateCreditScore = async () => {
  if (!hasAllRequiredConsent.value) return
  
  isCalculatingScore.value = true
  
  try {
    // Simulate credit score calculation
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Mock credit score calculation based on application data
    const score = Math.floor(Math.random() * 200) + 650 // 650-850 range
    const riskLevel = score >= 750 ? 'Low' : score >= 700 ? 'Medium' : 'High'
    const recommendedAmount = Math.floor(score * 10) // Simple calculation
    
    creditScore.value = {
      score,
      risk_level: riskLevel,
      recommended_amount: recommendedAmount,
      factors: [
        'Income stability',
        'Employment history',
        'Credit history',
        'Debt-to-income ratio',
        'Document verification'
      ]
    }
  } catch (error) {
    console.error('Error calculating credit score:', error)
  } finally {
    isCalculatingScore.value = false
  }
}

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
  
  if (!formData.loan_purpose) {
    errors.loan_purpose = 'Loan purpose is required'
    return false
  }
  
  if (!formData.loan_amount || formData.loan_amount < 100) {
    errors.loan_amount = 'Loan amount is required and must be at least $100'
    return false
  }
  
  if (!formData.loan_term_months) {
    errors.loan_term_months = 'Loan term is required'
    return false
  }
  
  return true
}

const handleSubmit = async () => {
  if (isReadOnly) {
    // In read-only mode, just navigate to next step without validation or submission
    const submissionData = {
      ...consent,  // Send consent fields at top level
      ...formData, // Send form data fields
      credit_score: creditScore.value,
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
    // Calculate credit score if not already done
    if (!creditScore.value) {
      await calculateCreditScore()
    }
    
    const submissionData = {
      ...consent,  // Send consent fields at top level
      ...formData, // Send form data fields
      credit_score: creditScore.value,
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
    
    // Handle form data fields
    if (data.loan_amount !== undefined) {
      formData.loan_amount = Number(data.loan_amount) || null
    }
    if (data.loan_term_months !== undefined) {
      formData.loan_term_months = data.loan_term_months
    }
    if (data.additional_notes !== undefined) {
      formData.additional_notes = data.additional_notes
    }
    if (data.credit_score_range !== undefined) {
      formData.credit_score_range = data.credit_score_range
    }
    if (data.risk_tolerance !== undefined) {
      formData.risk_tolerance = data.risk_tolerance
    }
    if (data.loan_purpose !== undefined) {
      formData.loan_purpose = data.loan_purpose
    }
    
    // Handle other fields
    if (data.credit_score) {
      creditScore.value = data.credit_score
    }
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