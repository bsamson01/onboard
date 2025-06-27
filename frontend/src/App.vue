<template>
  <div id="app">
    <div v-if="authStore.isLoading" class="min-h-screen flex items-center justify-center bg-gray-50">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-sm text-gray-600">Loading...</p>
      </div>
    </div>
    <router-view v-else />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// onMounted(() => {
//   // Check for existing token on app load
//   authStore.checkAuth()
// })
</script>