<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-2xl font-bold text-gray-900">External Services Configuration</h2>
      <button @click="$emit('refresh')" class="btn-secondary">
        <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Refresh
      </button>
    </div>

    <!-- Services List -->
    <div class="grid gap-6">
      <!-- Scorecard Service -->
      <div v-if="services.scorecard_service" class="border border-gray-200 rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-medium text-gray-900">{{ services.scorecard_service.name }}</h3>
            <div class="flex items-center space-x-3">
              <span :class="[
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                getStatusBadgeClass(services.scorecard_service.health_status?.status)
              ]">
                {{ getStatusText(services.scorecard_service.health_status?.status) }}
              </span>
              <button
                @click="$emit('test', 'scorecard')"
                class="btn-sm btn-outline"
                :disabled="!services.scorecard_service.is_enabled"
              >
                Test Connection
              </button>
              <button
                @click="$emit('configure', services.scorecard_service)"
                class="btn-sm btn-primary"
              >
                Configure
              </button>
            </div>
          </div>
        </div>

        <div class="p-6 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Service URL -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Service URL</label>
              <p class="mt-1 text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded">
                {{ services.scorecard_service.url || 'Not configured' }}
              </p>
            </div>

            <!-- API Key -->
            <div>
              <label class="block text-sm font-medium text-gray-700">API Key</label>
              <p class="mt-1 text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded">
                {{ services.scorecard_service.api_key || 'Not configured' }}
              </p>
            </div>

            <!-- Status -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Status</label>
              <div class="mt-1 flex items-center">
                <div :class="[
                  'w-3 h-3 rounded-full mr-2',
                  getStatusDotClass(services.scorecard_service.health_status?.status)
                ]"></div>
                <span class="text-sm text-gray-900">
                  {{ getStatusText(services.scorecard_service.health_status?.status) }}
                </span>
                <span v-if="services.scorecard_service.health_status?.response_time" class="text-sm text-gray-500 ml-2">
                  ({{ services.scorecard_service.health_status.response_time }})
                </span>
              </div>
            </div>

            <!-- Last Health Check -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Last Health Check</label>
              <p class="mt-1 text-sm text-gray-900">
                {{ formatDateTime(services.scorecard_service.last_health_check) }}
              </p>
            </div>
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <p class="mt-1 text-sm text-gray-600">
              {{ services.scorecard_service.description }}
            </p>
          </div>

          <!-- Health Status Details -->
          <div v-if="services.scorecard_service.health_status?.error" class="bg-red-50 border border-red-200 rounded-md p-4">
            <h4 class="text-sm font-medium text-red-800">Connection Error</h4>
            <p class="mt-1 text-sm text-red-700">
              {{ services.scorecard_service.health_status.error }}
            </p>
          </div>

          <!-- Configuration Status -->
          <div class="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg v-if="services.scorecard_service.is_enabled" class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                <svg v-else class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="ml-3">
                <h4 class="text-sm font-medium" :class="services.scorecard_service.is_enabled ? 'text-blue-800' : 'text-yellow-800'">
                  {{ services.scorecard_service.is_enabled ? 'Service Configured' : 'Service Needs Configuration' }}
                </h4>
                <p class="mt-1 text-sm" :class="services.scorecard_service.is_enabled ? 'text-blue-700' : 'text-yellow-700'">
                  {{ services.scorecard_service.is_enabled 
                      ? 'The scorecard service is properly configured and ready to use.' 
                      : 'Please configure the service URL and API key to enable credit scoring functionality.' }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Add New Service Button -->
      <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <svg class="h-12 w-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Add External Service</h3>
        <p class="text-sm text-gray-500 mb-4">
          Configure additional external services for your application
        </p>
        <button class="btn-primary" disabled>
          Coming Soon
        </button>
      </div>
    </div>

    <!-- Service Configuration Tips -->
    <div class="bg-gray-50 rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 mb-4">Configuration Tips</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
        <div>
          <h4 class="font-medium text-gray-900 mb-2">Scorecard Service</h4>
          <ul class="space-y-1">
            <li>• Ensure the service URL is accessible from your server</li>
            <li>• Verify the API key has proper permissions</li>
            <li>• Test the connection after configuration changes</li>
            <li>• Monitor health status regularly</li>
          </ul>
        </div>
        <div>
          <h4 class="font-medium text-gray-900 mb-2">Security Best Practices</h4>
          <ul class="space-y-1">
            <li>• Use HTTPS URLs for all external services</li>
            <li>• Rotate API keys regularly</li>
            <li>• Monitor for unauthorized access attempts</li>
            <li>• Keep service configurations up to date</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  services: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['configure', 'test', 'refresh'])

// Methods
const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'healthy':
      return 'bg-green-100 text-green-800'
    case 'unhealthy':
      return 'bg-red-100 text-red-800'
    case 'not_configured':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getStatusDotClass = (status) => {
  switch (status) {
    case 'healthy':
      return 'bg-green-400'
    case 'unhealthy':
      return 'bg-red-400'
    case 'not_configured':
      return 'bg-yellow-400'
    default:
      return 'bg-gray-400'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'healthy':
      return 'Healthy'
    case 'unhealthy':
      return 'Unhealthy'
    case 'not_configured':
      return 'Not Configured'
    default:
      return 'Unknown'
  }
}

const formatDateTime = (dateString) => {
  if (!dateString) return 'Never'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return 'Invalid date'
  }
}
</script>

<style scoped>
.btn-secondary {
  @apply inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}

.btn-primary {
  @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}

.btn-sm {
  @apply inline-flex items-center px-3 py-1.5 text-xs font-medium rounded;
}

.btn-outline {
  @apply border border-gray-300 text-gray-700 bg-white hover:bg-gray-50;
}
</style>