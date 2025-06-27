import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token'))
  const user = ref(null)
  const isLoading = ref(false)
  
  const isAuthenticated = computed(() => !!token.value)
  
  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login-json', { email, password })
      token.value = response.data.access_token
      user.value = response.data.user
      localStorage.setItem('token', token.value)
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      }
    }
  }
  
  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }
  
  const checkAuth = async () => {
    if (!token.value) return
    
    isLoading.value = true
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      console.log('user.value', user.value)
    } catch (error) {
      logout()
    } finally {
      isLoading.value = false
    }
  }
  
  return {
    token,
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    checkAuth
  }
})