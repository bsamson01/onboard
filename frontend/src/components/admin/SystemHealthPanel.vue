<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-medium text-gray-900">System Health</h3>
      <button 
        @click="$emit('refresh')"
        class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        Refresh
      </button>
    </div>

    <div v-if="healthData" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- Overall Status -->
      <div class="bg-white rounded-lg shadow p-6">
        <h4 class="text-sm font-medium text-gray-500">Overall Status</h4>
        <p class="text-2xl font-bold" :class="getStatusColor(healthData.status)">
          {{ healthData.status }}
        </p>
        <p class="text-sm text-gray-500 mt-1">Last checked: {{ formatDate(healthData.timestamp) }}</p>
      </div>

      <!-- Database Status -->
      <div class="bg-white rounded-lg shadow p-6">
        <h4 class="text-sm font-medium text-gray-500">Database</h4>
        <p class="text-2xl font-bold" :class="getStatusColor(healthData.database?.status)">
          {{ healthData.database?.status || 'Unknown' }}
        </p>
        <p class="text-sm text-gray-500 mt-1">{{ healthData.database?.details || 'No details available' }}</p>
      </div>

      <!-- API Status -->
      <div class="bg-white rounded-lg shadow p-6">
        <h4 class="text-sm font-medium text-gray-500">API Service</h4>
        <p class="text-2xl font-bold" :class="getStatusColor(healthData.services?.api?.status)">
          {{ healthData.services?.api?.status || 'Unknown' }}
        </p>
        <p class="text-sm text-gray-500 mt-1">{{ healthData.services?.api?.response_time || 'No data' }}</p>
      </div>
    </div>

    <!-- External Services -->
    <div v-if="healthData?.external_services" class="bg-white rounded-lg shadow">
      <div class="px-6 py-4 border-b border-gray-200">
        <h4 class="text-lg font-medium text-gray-900">External Services</h4>
      </div>
      <div class="p-6">
        <div class="space-y-4">
          <div v-for="(service, name) in healthData.external_services" :key="name" class="flex items-center justify-between">
            <div>
              <h5 class="text-sm font-medium text-gray-900">{{ formatServiceName(name) }}</h5>
              <p class="text-sm text-gray-500">{{ service.description || 'No description' }}</p>
            </div>
            <div class="flex items-center space-x-2">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    :class="getStatusBadgeClass(service.status)">
                {{ service.status }}
              </span>
              <span v-if="service.last_check" class="text-xs text-gray-500">
                {{ formatDate(service.last_check) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-2 text-sm text-gray-500">Loading system health data...</p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  healthData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['refresh'])

const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'healthy':
    case 'operational':
      return 'text-green-600'
    case 'degraded':
    case 'warning':
      return 'text-yellow-600'
    case 'unhealthy':
    case 'error':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

const getStatusBadgeClass = (status) => {
  switch (status?.toLowerCase()) {
    case 'healthy':
    case 'operational':
      return 'bg-green-100 text-green-800'
    case 'degraded':
    case 'warning':
      return 'bg-yellow-100 text-yellow-800'
    case 'unhealthy':
    case 'error':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const formatServiceName = (name) => {
  return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script> 