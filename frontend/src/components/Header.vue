<template>
  <header class="bg-white shadow-sm border-b sticky top-0 z-30 animate__animated animate__fadeInDown">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
      <div class="flex items-center">
        <router-link to="/" class="text-xl font-semibold text-blue-700 font-bold tracking-tight">Onboard</router-link>
        <span class="ml-4 text-gray-700 font-medium">MicroFinance Platform</span>
      </div>
      <div class="flex items-center space-x-4">
        <span v-if="user" class="text-sm text-gray-700 font-medium">Welcome, {{ user.first_name }}</span>
        <button v-if="user" @click="$emit('logout')" class="btn-secondary">Logout</button>
        <template v-else>
          <button @click="$router.push('/signup')" class="btn-primary">Sign Up</button>
          <router-link to="/login" class="btn-secondary">Login</router-link>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
const user = computed(() => authStore.user)
const isStaff = computed(() => ['admin', 'loan_officer', 'risk_officer'].includes(user.value?.role))
</script>

<style scoped>
.btn-primary {
  @apply bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded shadow transition-all;
}
.btn-secondary {
  @apply bg-white border border-blue-600 text-blue-600 font-semibold py-2 px-4 rounded shadow hover:bg-blue-50 transition-all;
}
</style> 