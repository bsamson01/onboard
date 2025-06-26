<template>
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="closeModal">
    <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white" @click.stop>
      <!-- Modal Header -->
      <div class="flex justify-between items-center pb-4 border-b border-gray-200">
        <h3 class="text-lg font-medium text-gray-900">
          Configure {{ service?.name || 'Service' }}
        </h3>
        <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
          <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="py-6">
        <form @submit.prevent="saveConfiguration" class="space-y-6">
          <!-- Service URL -->
          <div>
            <label for="serviceUrl" class="block text-sm font-medium text-gray-700">
              Service URL *
            </label>
            <div class="mt-1">
              <input
                id="serviceUrl"
                v-model="form.scorecard_api_url"
                type="url"
                required
                class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://api.scorecard-service.com"
              />
            </div>
            <p class="mt-1 text-sm text-gray-500">
              The base URL for the external service API
            </p>
          </div>

          <!-- API Key -->
          <div>
            <label for="apiKey" class="block text-sm font-medium text-gray-700">
              API Key *
            </label>
            <div class="mt-1 relative">
              <input
                id="apiKey"
                v-model="form.scorecard_api_key"
                :type="showApiKey ? 'text' : 'password'"
                required
                class="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter API key"
              />
              <button
                type="button"
                @click="showApiKey = !showApiKey"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                <svg v-if="showApiKey" class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L12 12m-3.172-3.172a4 4 0 015.656 0L21 21" />
                </svg>
                <svg v-else class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
            </div>
            <p class="mt-1 text-sm text-gray-500">
              The API key provided by the service provider
            </p>
          </div>

          <!-- Timeout -->
          <div>
            <label for="timeout" class="block text-sm font-medium text-gray-700">
              Timeout (seconds)
            </label>
            <div class="mt-1">
              <input
                id="timeout"
                v-model.number="form.scorecard_timeout"
                type="number"
                min="5"
                max="120"
                class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <p class="mt-1 text-sm text-gray-500">
              Request timeout in seconds (5-120)
            </p>
          </div>

          <!-- Test Connection Section -->
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="flex items-center justify-between mb-3">
              <h4 class="text-sm font-medium text-gray-900">Connection Test</h4>
              <button
                type="button"
                @click="testConnection"
                :disabled="isTestingConnection || !isFormValid"
                class="btn-sm btn-outline"
              >
                <svg v-if="isTestingConnection" class="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ isTestingConnection ? 'Testing...' : 'Test Connection' }}
              </button>
            </div>

            <!-- Test Results -->
            <div v-if="testResult" class="mt-3">
              <div :class="[
                'rounded-md p-3',
                testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
              ]">
                <div class="flex">
                  <div class="flex-shrink-0">
                    <svg v-if="testResult.success" class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                    <svg v-else class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L10 11.414l1.293-1.293a1 1 0 001.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                  </div>
                  <div class="ml-3">
                    <h5 :class="[
                      'text-sm font-medium',
                      testResult.success ? 'text-green-800' : 'text-red-800'
                    ]">
                      {{ testResult.success ? 'Connection Successful' : 'Connection Failed' }}
                    </h5>
                    <p :class="[
                      'mt-1 text-sm',
                      testResult.success ? 'text-green-700' : 'text-red-700'
                    ]">
                      {{ testResult.message || testResult.error }}
                    </p>
                    <div v-if="testResult.response_time" class="mt-1 text-xs text-gray-600">
                      Response time: {{ testResult.response_time }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <p class="mt-2 text-xs text-gray-600">
              It's recommended to test the connection before saving the configuration.
            </p>
          </div>

          <!-- Current Configuration Info -->
          <div v-if="service" class="bg-blue-50 rounded-lg p-4">
            <h4 class="text-sm font-medium text-blue-900 mb-2">Current Configuration</h4>
            <div class="text-sm text-blue-800 space-y-1">
              <p><span class="font-medium">URL:</span> {{ service.url || 'Not set' }}</p>
              <p><span class="font-medium">API Key:</span> {{ service.api_key || 'Not set' }}</p>
              <p><span class="font-medium">Status:</span> {{ service.health_status?.status || 'Unknown' }}</p>
            </div>
          </div>

          <!-- Form Validation Errors -->
          <div v-if="validationErrors.length > 0" class="bg-red-50 border border-red-200 rounded-md p-4">
            <h4 class="text-sm font-medium text-red-800">Please fix the following errors:</h4>
            <ul class="mt-2 text-sm text-red-700 list-disc list-inside">
              <li v-for="error in validationErrors" :key="error">{{ error }}</li>
            </ul>
          </div>
        </form>
      </div>

      <!-- Modal Footer -->
      <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          @click="closeModal"
          class="btn-secondary"
        >
          Cancel
        </button>
        <button
          @click="saveConfiguration"
          :disabled="isSaving || !isFormValid"
          class="btn-primary"
        >
          <svg v-if="isSaving" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isSaving ? 'Saving...' : 'Save Configuration' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/services/api'

const props = defineProps({
  service: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

// Reactive data
const showApiKey = ref(false)
const isSaving = ref(false)
const isTestingConnection = ref(false)
const testResult = ref(null)

const form = ref({
  scorecard_api_url: '',
  scorecard_api_key: '',
  scorecard_timeout: 30
})

// Computed properties
const isFormValid = computed(() => {
  return form.value.scorecard_api_url && 
         form.value.scorecard_api_key && 
         form.value.scorecard_timeout >= 5 && 
         form.value.scorecard_timeout <= 120
})

const validationErrors = computed(() => {
  const errors = []
  
  if (!form.value.scorecard_api_url) {
    errors.push('Service URL is required')
  } else {
    try {
      new URL(form.value.scorecard_api_url)
    } catch {
      errors.push('Service URL must be a valid URL')
    }
  }
  
  if (!form.value.scorecard_api_key) {
    errors.push('API Key is required')
  }
  
  if (form.value.scorecard_timeout < 5 || form.value.scorecard_timeout > 120) {
    errors.push('Timeout must be between 5 and 120 seconds')
  }
  
  return errors
})

// Methods
const closeModal = () => {
  emit('close')
}

const testConnection = async () => {
  if (!isFormValid.value) return
  
  try {
    isTestingConnection.value = true
    testResult.value = null
    
    // Create a test configuration to send to the backend
    const testConfig = {
      scorecard_api_url: form.value.scorecard_api_url,
      scorecard_api_key: form.value.scorecard_api_key,
      scorecard_timeout: form.value.scorecard_timeout
    }
    
    // This would be a separate endpoint for testing configurations
    const response = await api.post('/admin/external-services/scorecard/test-config', testConfig)
    testResult.value = response.data
    
  } catch (error) {
    testResult.value = {
      success: false,
      error: error.response?.data?.detail || 'Connection test failed'
    }
  } finally {
    isTestingConnection.value = false
  }
}

const saveConfiguration = async () => {
  if (!isFormValid.value) return
  
  try {
    isSaving.value = true
    
    await emit('save', form.value)
    
  } catch (error) {
    console.error('Failed to save configuration:', error)
  } finally {
    isSaving.value = false
  }
}

// Initialize form with current service data
const initializeForm = () => {
  if (props.service) {
    form.value.scorecard_api_url = props.service.url || ''
    form.value.scorecard_api_key = '' // Don't pre-fill for security
    form.value.scorecard_timeout = props.service.timeout || 30
  }
}

// Watch for service changes
watch(() => props.service, initializeForm, { immediate: true })

// Clear test result when form changes
watch(form, () => {
  testResult.value = null
}, { deep: true })

// Lifecycle
onMounted(() => {
  initializeForm()
})
</script>

<style scoped>
.btn-secondary {
  @apply inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}

.btn-primary {
  @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-sm {
  @apply inline-flex items-center px-3 py-1.5 text-xs font-medium rounded;
}

.btn-outline {
  @apply border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed;
}
</style>