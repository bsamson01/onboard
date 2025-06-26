<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-medium text-gray-900">Audit Logs</h3>
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

    <div v-if="logs.length > 0" class="bg-white shadow overflow-hidden sm:rounded-md">
      <ul class="divide-y divide-gray-200">
        <li v-for="log in logs" :key="log.id" class="px-6 py-4">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-2">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getActionBadgeClass(log.action)">
                  {{ formatAction(log.action) }}
                </span>
                <span class="text-sm text-gray-500">
                  {{ formatDate(log.created_at) }}
                </span>
              </div>
              <div class="mt-1">
                <p class="text-sm text-gray-900">
                  <span class="font-medium">{{ log.user_name || 'System' }}</span>
                  {{ getActionDescription(log.action) }}
                  <span v-if="log.resource_type" class="font-medium">{{ log.resource_type }}</span>
                  <span v-if="log.resource_id" class="text-gray-500">(ID: {{ log.resource_id }})</span>
                </p>
                <p v-if="log.details" class="text-sm text-gray-500 mt-1">
                  {{ log.details }}
                </p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span v-if="log.ip_address" class="text-xs text-gray-400">
                {{ log.ip_address }}
              </span>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
      </svg>
      <h3 class="mt-4 text-lg font-medium text-gray-900">No audit logs found</h3>
      <p class="mt-2 text-gray-500">No audit logs are currently available.</p>
    </div>

    <!-- Loading State -->
    <div v-if="!logs && logs.length === 0" class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-2 text-sm text-gray-500">Loading audit logs...</p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['refresh'])

const getActionBadgeClass = (action) => {
  const actionType = action?.toLowerCase()
  if (actionType?.includes('create') || actionType?.includes('login')) {
    return 'bg-green-100 text-green-800'
  } else if (actionType?.includes('update') || actionType?.includes('modify')) {
    return 'bg-blue-100 text-blue-800'
  } else if (actionType?.includes('delete') || actionType?.includes('logout')) {
    return 'bg-red-100 text-red-800'
  } else if (actionType?.includes('security') || actionType?.includes('audit')) {
    return 'bg-purple-100 text-purple-800'
  } else {
    return 'bg-gray-100 text-gray-800'
  }
}

const formatAction = (action) => {
  if (!action) return 'Unknown'
  return action.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

const getActionDescription = (action) => {
  const actionType = action?.toLowerCase()
  if (actionType?.includes('create')) {
    return 'created'
  } else if (actionType?.includes('update')) {
    return 'updated'
  } else if (actionType?.includes('delete')) {
    return 'deleted'
  } else if (actionType?.includes('login')) {
    return 'logged in'
  } else if (actionType?.includes('logout')) {
    return 'logged out'
  } else if (actionType?.includes('submit')) {
    return 'submitted'
  } else if (actionType?.includes('approve')) {
    return 'approved'
  } else if (actionType?.includes('reject')) {
    return 'rejected'
  } else {
    return 'performed action on'
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'Unknown time'
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script> 