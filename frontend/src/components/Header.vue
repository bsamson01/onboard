<template>
  <header class="bg-white shadow sticky top-0 z-30">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
      <div class="flex items-center gap-4">
        <router-link to="/" class="text-xl font-bold text-blue-700">Onboard</router-link>
      </div>
      <div class="flex items-center gap-4">
        <span v-if="user" class="text-sm text-gray-700 font-medium">Welcome, {{ user.first_name }}</span>
        <button v-if="user" @click="$emit('logout')" class="text-sm text-gray-500 hover:text-red-600 font-medium">Logout</button>
        <router-link v-else to="/login" class="text-sm text-blue-600 hover:underline font-medium">Login</router-link>
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