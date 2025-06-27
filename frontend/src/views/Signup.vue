<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-blue-700">
          Create your account
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Start your microfinance journey today
        </p>
      </div>
      <form class="mt-8 space-y-6" @submit.prevent="submit">
        <div>
          <label class="form-label">First Name</label>
          <input v-model="form.first_name" type="text" required class="form-input" placeholder="First Name" />
        </div>
        <div>
          <label class="form-label">Last Name</label>
          <input v-model="form.last_name" type="text" required class="form-input" placeholder="Last Name" />
        </div>
        <div>
          <label class="form-label">Email</label>
          <input v-model="form.email" type="email" required class="form-input" placeholder="Email" />
        </div>
        <div>
          <label class="form-label">Username</label>
          <input v-model="form.username" type="text" required minlength="3" class="form-input" placeholder="Username" />
        </div>
        <div>
          <label class="form-label">Password</label>
          <input v-model="form.password" type="password" required minlength="8" class="form-input" placeholder="Password" />
        </div>
        <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 rounded p-2 text-sm">{{ error }}</div>
        <div v-if="success" class="bg-green-50 border border-green-200 text-green-700 rounded p-2 text-sm">Account created! You can now sign in.</div>
        <button type="submit" class="w-full btn-primary" :disabled="loading">
          <span v-if="loading" class="animate-spin mr-2">⏳</span>
          Sign Up
        </button>
      </form>
      <div class="mt-6 text-center">
        <span class="text-gray-600">Already have an account?</span>
        <router-link to="/login" class="text-blue-600 hover:underline font-semibold ml-1">Login</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({
  email: '',
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  role: 'CUSTOMER',
})
const loading = ref(false)
const error = ref('')
const success = ref(false)

const submit = async () => {
  error.value = ''
  success.value = false
  loading.value = true
  try {
    await axios.post('/api/v1/auth/register', form.value)
    success.value = true
    form.value = { email: '', username: '', password: '', first_name: '', last_name: '', role: 'CUSTOMER' }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Registration failed.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}
.form-input {
  @apply block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 mb-2;
}
.btn-primary {
  @apply bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded shadow;
}
</style> 