<template>
  <div class="min-h-screen bg-gray-50 py-8 px-2 sm:px-6 lg:px-8">
    <div class="max-w-3xl mx-auto">
      <h1 class="text-2xl font-bold mb-6 text-gray-900">All Activities</h1>
      <div class="relative py-4 space-y-2">
        <div v-for="activity in activities" :key="activity.timestamp + activity.label" class="relative bg-white rounded-xl shadow p-4 flex flex-col gap-1 border border-gray-100">
          <div class="flex flex-wrap items-center gap-2 mb-1">
            <span :class="[
              'inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold',
              activity.label === 'Application Submitted' ? 'bg-blue-100 text-blue-700' :
              activity.label === 'Application Created' ? 'bg-green-100 text-green-700' :
              activity.label === 'Step Completed' ? 'bg-yellow-100 text-yellow-700' :
              activity.label === 'Document Uploaded' ? 'bg-purple-100 text-purple-700' :
              activity.label === 'Credit Score Calculated' ? 'bg-indigo-100 text-indigo-700' :
              'bg-gray-100 text-gray-700'
            ]">
              {{ activity.label }}
            </span>
            <span v-if="activity.user_display" class="font-bold text-sm text-gray-900">{{ activity.user_display }}</span>
            <span v-if="activity.application_number" class="px-2 py-0.5 rounded bg-gray-100 text-gray-500 text-xs font-medium">App #{{ activity.application_number }}</span>
          </div>
          <div class="text-xs text-gray-700">{{ activity.description }}</div>
          <div class="text-xs text-gray-400 mt-1">{{ formatDate(activity.timestamp) }}</div>
        </div>
        <div v-if="activities.length === 0" class="text-gray-400">No activities found.</div>
      </div>
      <div class="flex justify-between items-center mt-6">
        <button @click="prevPage" :disabled="offset === 0" class="px-4 py-2 rounded bg-gray-200 text-gray-700 font-medium disabled:opacity-50">Previous</button>
        <span class="text-xs text-gray-500">Page {{ page }}</span>
        <button @click="nextPage" :disabled="activities.length < limit" class="px-4 py-2 rounded bg-blue-600 text-white font-medium disabled:opacity-50">Next</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const activities = ref([])
const limit = 10
const offset = ref(0)
const page = ref(1)

function formatDate(dateString) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

async function fetchActivities() {
  const response = await api.get(`/admin/staff/activities?limit=${limit}&offset=${offset.value}`)
  activities.value = response.data.activities
}

function nextPage() {
  offset.value += limit
  page.value += 1
  fetchActivities()
}

function prevPage() {
  if (offset.value >= limit) {
    offset.value -= limit
    page.value -= 1
    fetchActivities()
  }
}

onMounted(fetchActivities)
</script> 