<template>
  <div class="space-y-8">
    <div class="text-center">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">Document Upload</h2>
      <p class="text-lg text-gray-600">Please upload the required documents for verification</p>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-8">
      <!-- Required Documents -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          Required Documents
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Government ID -->
          <div class="space-y-3">
            <label class="block text-sm font-semibold text-gray-700">
              Government ID (Passport/Driver's License) *
            </label>
            <div class="flex justify-center px-6 pt-8 pb-8 border-2 border-gray-300 border-dashed rounded-lg hover:border-blue-400 transition-all duration-200 bg-gray-50 hover:bg-blue-50">
              <div class="space-y-3 text-center">
                <svg class="mx-auto h-16 w-16 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <div class="flex text-sm text-gray-600 justify-center">
                  <label for="government_id" class="relative cursor-pointer bg-white rounded-md font-semibold text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500 px-4 py-2 border border-blue-300 hover:border-blue-400 transition-all duration-200">
                    <span>Upload a file</span>
                    <input
                      id="government_id"
                      ref="governmentIdInput"
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      :disabled="isReadOnly"
                      @change="handleFileUpload('government_id', $event)"
                      class="sr-only"
                    />
                  </label>
                  <p class="pl-3 self-center">or drag and drop</p>
                </div>
                <p class="text-xs text-gray-500">PDF, JPG, PNG up to 10MB</p>
              </div>
            </div>
            <div v-if="uploadedFiles.government_id" class="flex items-center text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg">
              <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              {{ uploadedFiles.government_id.name }}
            </div>
            <p v-if="errors.government_id" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.government_id }}
            </p>
          </div>

          <!-- Proof of Address -->
          <div class="space-y-3">
            <label class="block text-sm font-semibold text-gray-700">
              Proof of Address (Utility Bill/Bank Statement) *
            </label>
            <div class="flex justify-center px-6 pt-8 pb-8 border-2 border-gray-300 border-dashed rounded-lg hover:border-blue-400 transition-all duration-200 bg-gray-50 hover:bg-blue-50">
              <div class="space-y-3 text-center">
                <svg class="mx-auto h-16 w-16 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <div class="flex text-sm text-gray-600 justify-center">
                  <label for="proof_of_address" class="relative cursor-pointer bg-white rounded-md font-semibold text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500 px-4 py-2 border border-blue-300 hover:border-blue-400 transition-all duration-200">
                    <span>Upload a file</span>
                    <input
                      id="proof_of_address"
                      ref="proofOfAddressInput"
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      :disabled="isReadOnly"
                      @change="handleFileUpload('proof_of_address', $event)"
                      class="sr-only"
                    />
                  </label>
                  <p class="pl-3 self-center">or drag and drop</p>
                </div>
                <p class="text-xs text-gray-500">PDF, JPG, PNG up to 10MB</p>
              </div>
            </div>
            <div v-if="uploadedFiles.proof_of_address" class="flex items-center text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg">
              <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              {{ uploadedFiles.proof_of_address.name }}
            </div>
            <p v-if="errors.proof_of_address" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.proof_of_address }}
            </p>
          </div>
        </div>
      </div>

      <!-- Optional Documents -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          Optional Documents
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Bank Statement -->
          <div class="space-y-3">
            <label class="block text-sm font-semibold text-gray-700">
              Bank Statement (Last 3 months)
            </label>
            <div class="flex justify-center px-6 pt-8 pb-8 border-2 border-gray-300 border-dashed rounded-lg hover:border-blue-400 transition-all duration-200 bg-gray-50 hover:bg-blue-50">
              <div class="space-y-3 text-center">
                <svg class="mx-auto h-16 w-16 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <div class="flex text-sm text-gray-600 justify-center">
                  <label for="bank_statement" class="relative cursor-pointer bg-white rounded-md font-semibold text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500 px-4 py-2 border border-blue-300 hover:border-blue-400 transition-all duration-200">
                    <span>Upload a file</span>
                    <input
                      id="bank_statement"
                      ref="bankStatementInput"
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      :disabled="isReadOnly"
                      @change="handleFileUpload('bank_statement', $event)"
                      class="sr-only"
                    />
                  </label>
                  <p class="pl-3 self-center">or drag and drop</p>
                </div>
                <p class="text-xs text-gray-500">PDF, JPG, PNG up to 10MB</p>
              </div>
            </div>
            <div v-if="uploadedFiles.bank_statement" class="flex items-center text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg">
              <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              {{ uploadedFiles.bank_statement.name }}
            </div>
          </div>

          <!-- Pay Stub -->
          <div class="space-y-3">
            <label class="block text-sm font-semibold text-gray-700">
              Recent Pay Stub
            </label>
            <div class="flex justify-center px-6 pt-8 pb-8 border-2 border-gray-300 border-dashed rounded-lg hover:border-blue-400 transition-all duration-200 bg-gray-50 hover:bg-blue-50">
              <div class="space-y-3 text-center">
                <svg class="mx-auto h-16 w-16 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <div class="flex text-sm text-gray-600 justify-center">
                  <label for="pay_stub" class="relative cursor-pointer bg-white rounded-md font-semibold text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500 px-4 py-2 border border-blue-300 hover:border-blue-400 transition-all duration-200">
                    <span>Upload a file</span>
                    <input
                      id="pay_stub"
                      ref="payStubInput"
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      :disabled="isReadOnly"
                      @change="handleFileUpload('pay_stub', $event)"
                      class="sr-only"
                    />
                  </label>
                  <p class="pl-3 self-center">or drag and drop</p>
                </div>
                <p class="text-xs text-gray-500">PDF, JPG, PNG up to 10MB</p>
              </div>
            </div>
            <div v-if="uploadedFiles.pay_stub" class="flex items-center text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg">
              <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              {{ uploadedFiles.pay_stub.name }}
            </div>
          </div>
        </div>
      </div>

      <!-- Document Guidelines -->
      <div class="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h4 class="text-lg font-semibold text-blue-800 mb-3 flex items-center">
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          Document Guidelines
        </h4>
        <ul class="text-sm text-blue-700 space-y-2">
          <li class="flex items-start">
            <svg class="w-4 h-4 mr-2 mt-0.5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            All documents must be clear and legible
          </li>
          <li class="flex items-start">
            <svg class="w-4 h-4 mr-2 mt-0.5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            Government ID must be current and not expired
          </li>
          <li class="flex items-start">
            <svg class="w-4 h-4 mr-2 mt-0.5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            Proof of address must be dated within the last 3 months
          </li>
          <li class="flex items-start">
            <svg class="w-4 h-4 mr-2 mt-0.5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            Bank statements should show your name and address
          </li>
          <li class="flex items-start">
            <svg class="w-4 h-4 mr-2 mt-0.5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            Maximum file size: 10MB per document
          </li>
          <li class="flex items-start">
            <svg class="w-4 h-4 mr-2 mt-0.5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            Accepted formats: PDF, JPG, JPEG, PNG
          </li>
        </ul>
      </div>

      <!-- Error Display -->
      <div v-if="errors.upload" class="bg-red-50 border border-red-200 rounded-xl p-6">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Upload Error</h3>
            <p class="mt-1 text-sm text-red-700">{{ errors.upload }}</p>
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
          :disabled="isSubmitting || (!hasRequiredDocuments && !isReadOnly)"
          class="px-6 py-3 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          <span v-if="isSubmitting" class="flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Uploading...
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
import { onboardingService } from '@/services/onboarding'

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

const uploadedFiles = reactive({
  government_id: null,
  proof_of_address: null,
  bank_statement: null,
  pay_stub: null
})

const uploadedDocuments = reactive({
  government_id: null,
  proof_of_address: null,
  bank_statement: null,
  pay_stub: null
})

const hasRequiredDocuments = computed(() => {
  return uploadedFiles.government_id && uploadedFiles.proof_of_address
})

const validateFile = (file) => {
  const maxSize = 10 * 1024 * 1024 // 10MB
  const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
  
  if (file.size > maxSize) {
    return 'File size must be less than 10MB'
  }
  
  if (!allowedTypes.includes(file.type)) {
    return 'File type must be PDF, JPG, JPEG, or PNG'
  }
  
  return null
}

const handleFileUpload = (field, event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const error = validateFile(file)
  if (error) {
    errors[field] = error
    return
  }
  
  uploadedFiles[field] = file
  errors[field] = null
}

const validateForm = () => {
  errors.value = {}
  
  if (!uploadedFiles.government_id) {
    errors.government_id = 'Government ID is required'
  }
  
  if (!uploadedFiles.proof_of_address) {
    errors.proof_of_address = 'Proof of address is required'
  }
  
  return Object.keys(errors.value).length === 0
}

const uploadDocument = async (file, documentType) => {
  try {
    const response = await onboardingService.uploadDocument(
      props.application.id, 
      documentType, 
      file
    )
    return response.data
  } catch (error) {
    console.error(`Error uploading ${documentType}:`, error)
    throw error
  }
}

const handleSubmit = async () => {
  if (isReadOnly) {
    // In read-only mode, just navigate to next step without validation or submission
    emit('next', { documents: uploadedDocuments.value })
    return
  }
  
  if (!hasRequiredDocuments.value) {
    return
  }
  
  isSubmitting.value = true
  
  try {
    emit('next', { documents: uploadedDocuments.value })
  } catch (error) {
    console.error('Error submitting documents:', error)
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  // Load existing data if available
  if (props.stepData && Object.keys(props.stepData).length > 0) {
    // Handle existing uploaded documents
    if (props.stepData.documents) {
      Object.assign(uploadedDocuments, props.stepData.documents)
    }
    
    // Handle existing uploaded files info
    if (props.stepData.uploaded_files) {
      Object.keys(props.stepData.uploaded_files).forEach(key => {
        if (props.stepData.uploaded_files[key]) {
          // Create a mock file object for display
          uploadedFiles[key] = {
            name: props.stepData.uploaded_files[key]
          }
        }
      })
    }
  }
})
</script> 