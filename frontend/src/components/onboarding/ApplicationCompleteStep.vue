<template>
  <div class="max-w-2xl mx-auto">
    <!-- Success Header -->
    <div class="text-center mb-8">
      <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-6">
        <svg class="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
      </div>
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Application Submitted!</h1>
      <p class="text-lg text-gray-600">
        Your loan application has been successfully submitted and is now under review.
      </p>
    </div>

    <!-- Application Details -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
      <h2 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
        <svg class="w-6 h-6 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        Application Details
      </h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-500">Application Number</label>
            <p class="text-lg font-semibold text-gray-900">{{ application?.application_number || 'N/A' }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-500">Submission Date</label>
            <p class="text-lg font-semibold text-gray-900">{{ formatDate(new Date()) }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-500">Status</label>
            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
              </svg>
              Under Review
            </span>
          </div>
        </div>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-500">Requested Amount</label>
            <p class="text-lg font-semibold text-gray-900">{{ formatCurrency(applicationSummary?.loan_amount) }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-500">Loan Term</label>
            <p class="text-lg font-semibold text-gray-900">{{ applicationSummary?.loan_term_months }} months</p>
          </div>
          <div v-if="creditScore">
            <label class="block text-sm font-medium text-gray-500">Credit Score</label>
            <p class="text-lg font-semibold" :class="getCreditScoreColor(creditScore.score)">
              {{ creditScore.score }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Next Steps -->
    <div class="bg-blue-50 border border-blue-200 rounded-xl p-8 mb-8">
      <h3 class="text-xl font-semibold text-blue-900 mb-6 flex items-center">
        <svg class="w-6 h-6 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        What Happens Next?
      </h3>
      
      <div class="space-y-4">
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <div class="flex items-center justify-center h-8 w-8 rounded-full bg-blue-100">
              <span class="text-sm font-semibold text-blue-600">1</span>
            </div>
          </div>
          <div class="ml-4">
            <h4 class="text-sm font-semibold text-blue-900">Document Review</h4>
            <p class="text-sm text-blue-700 mt-1">Our team will review your submitted documents and verify your information.</p>
          </div>
        </div>
        
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <div class="flex items-center justify-center h-8 w-8 rounded-full bg-blue-100">
              <span class="text-sm font-semibold text-blue-600">2</span>
            </div>
          </div>
          <div class="ml-4">
            <h4 class="text-sm font-semibold text-blue-900">Credit Assessment</h4>
            <p class="text-sm text-blue-700 mt-1">We'll conduct a comprehensive credit assessment based on your financial profile.</p>
          </div>
        </div>
        
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <div class="flex items-center justify-center h-8 w-8 rounded-full bg-blue-100">
              <span class="text-sm font-semibold text-blue-600">3</span>
            </div>
          </div>
          <div class="ml-4">
            <h4 class="text-sm font-semibold text-blue-900">Decision & Notification</h4>
            <p class="text-sm text-blue-700 mt-1">You'll receive a decision within 3-5 business days via email and SMS.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Contact Information -->
    <div class="bg-gray-50 border border-gray-200 rounded-xl p-8 mb-8">
      <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
        <svg class="w-6 h-6 mr-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
        </svg>
        Need Help?
      </h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 class="text-sm font-semibold text-gray-900 mb-2">Customer Support</h4>
          <p class="text-sm text-gray-600 mb-2">Our support team is available to help you with any questions.</p>
          <div class="space-y-1">
            <p class="text-sm text-gray-600">
              <span class="font-medium">Phone:</span> +1 (555) 123-4567
            </p>
            <p class="text-sm text-gray-600">
              <span class="font-medium">Email:</span> support@microfinance.com
            </p>
            <p class="text-sm text-gray-600">
              <span class="font-medium">Hours:</span> Mon-Fri 9AM-6PM EST
            </p>
          </div>
        </div>
        
        <div>
          <h4 class="text-sm font-semibold text-gray-900 mb-2">Application Status</h4>
          <p class="text-sm text-gray-600 mb-2">Track your application status and receive updates.</p>
          <button
            @click="checkStatus"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
            </svg>
            Check Status
          </button>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="flex flex-col sm:flex-row gap-4 justify-center">
      <button
        @click="goToDashboard"
        class="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
      >
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path>
        </svg>
        Go to Dashboard
      </button>
      
      <button
        @click="downloadReceipt"
        class="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
      >
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        Download Receipt
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  application: {
    type: Object,
    default: null
  },
  stepData: {
    type: Object,
    default: () => ({})
  }
})

const router = useRouter()

const applicationSummary = computed(() => {
  return props.stepData?.application_summary || {}
})

const creditScore = computed(() => {
  return props.stepData?.credit_score || null
})

const formatDate = (date) => {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatCurrency = (amount) => {
  if (!amount) return '$0.00'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount)
}

const getCreditScoreColor = (score) => {
  if (score >= 750) return 'text-green-600'
  if (score >= 700) return 'text-blue-600'
  if (score >= 650) return 'text-yellow-600'
  return 'text-red-600'
}

const checkStatus = () => {
  // Navigate to application status page
  router.push(`/application-status?app=${props.application?.id}`)
}

const goToDashboard = () => {
  router.push('/')
}

const downloadReceipt = () => {
  // Create a simple receipt for download
  const receipt = `
Application Receipt
==================
Application Number: ${props.application?.application_number || 'N/A'}
Submission Date: ${formatDate(new Date())}
Status: Submitted for Review

Requested Amount: ${formatCurrency(applicationSummary.value?.loan_amount)}
Loan Term: ${applicationSummary.value?.loan_term_months || 'N/A'} months

Thank you for your application!
  `.trim()

  const blob = new Blob([receipt], { type: 'text/plain' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `application-receipt-${props.application?.application_number || 'receipt'}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}
</script> 