<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-semibold text-gray-900">MicroFinance Platform</h1>
          </div>
          <div class="flex items-center space-x-4">
            <button
              v-if="!authStore.isAuthenticated"
              @click="router.push('/login')"
              class="btn-primary"
            >
              Sign In
            </button>
            <div v-else class="flex items-center space-x-4">
              <span class="text-sm text-gray-700">Welcome, {{ authStore.user?.first_name }}!</span>
              <button @click="authStore.logout" class="btn-secondary">
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Hero Section -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20">
      <div class="text-center">
        <h1 class="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
          Your Financial Journey
          <span class="text-blue-600">Starts Here</span>
        </h1>
        <p class="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
          Complete our streamlined onboarding process to access personalized microfinance solutions 
          tailored to your needs.
        </p>
        <div class="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
          <div class="rounded-md shadow">
            <button
              v-if="authStore.isAuthenticated"
              @click="startOnboarding"
              class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg md:px-10"
            >
              Start Application
            </button>
            <button
              v-else
              @click="router.push('/login')"
              class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg md:px-10"
            >
              Get Started
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Features Section -->
    <div class="py-12 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="lg:text-center">
          <h2 class="text-base text-blue-600 font-semibold tracking-wide uppercase">Features</h2>
          <p class="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Simple, Secure, Fast
          </p>
        </div>

        <div class="mt-10">
          <div class="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-3">
            <!-- Feature 1 -->
            <div class="flex flex-col items-center text-center">
              <div class="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <h3 class="mt-4 text-lg font-medium text-gray-900">Quick Verification</h3>
              <p class="mt-2 text-sm text-gray-500">
                Upload your documents and get instant OCR processing with automated data extraction.
              </p>
            </div>

            <!-- Feature 2 -->
            <div class="flex flex-col items-center text-center">
              <div class="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <h3 class="mt-4 text-lg font-medium text-gray-900">Credit Scoring</h3>
              <p class="mt-2 text-sm text-gray-500">
                Get instant credit assessment with transparent scoring and personalized recommendations.
              </p>
            </div>

            <!-- Feature 3 -->
            <div class="flex flex-col items-center text-center">
              <div class="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                </svg>
              </div>
              <h3 class="mt-4 text-lg font-medium text-gray-900">Secure Process</h3>
              <p class="mt-2 text-sm text-gray-500">
                All data is encrypted and stored securely with full audit trails for transparency.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Process Steps -->
    <div class="py-12 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="lg:text-center">
          <h2 class="text-base text-blue-600 font-semibold tracking-wide uppercase">Process</h2>
          <p class="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            5 Simple Steps
          </p>
        </div>

        <div class="mt-10">
          <div class="grid grid-cols-1 gap-8 md:grid-cols-5">
            <div class="text-center">
              <div class="progress-step completed mx-auto">1</div>
              <h4 class="mt-2 font-medium">Personal Info</h4>
              <p class="text-sm text-gray-500">Basic personal details</p>
            </div>
            <div class="text-center">
              <div class="progress-step pending mx-auto">2</div>
              <h4 class="mt-2 font-medium">Contact Info</h4>
              <p class="text-sm text-gray-500">Address and contacts</p>
            </div>
            <div class="text-center">
              <div class="progress-step pending mx-auto">3</div>
              <h4 class="mt-2 font-medium">Financial Profile</h4>
              <p class="text-sm text-gray-500">Income and employment</p>
            </div>
            <div class="text-center">
              <div class="progress-step pending mx-auto">4</div>
              <h4 class="mt-2 font-medium">Documents</h4>
              <p class="text-sm text-gray-500">Upload ID documents</p>
            </div>
            <div class="text-center">
              <div class="progress-step pending mx-auto">5</div>
              <h4 class="mt-2 font-medium">Review</h4>
              <p class="text-sm text-gray-500">Consent and scoring</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onboardingService } from '@/services/onboarding'

const router = useRouter()
const authStore = useAuthStore()

const startOnboarding = async () => {
  try {
    // Check if user already has an active application
    const applicationsResponse = await onboardingService.getApplications()
    const activeApplication = applicationsResponse.data.find(app => 
      ['draft', 'in_progress', 'pending_documents'].includes(app.status)
    )
    
    if (activeApplication) {
      // Continue existing application
      router.push(`/onboarding?app=${activeApplication.id}`)
    } else {
      // Create new application
      const response = await onboardingService.createApplication()
      router.push(`/onboarding?app=${response.data.id}`)
    }
  } catch (error) {
    console.error('Failed to start onboarding:', error)
    // Handle error - maybe show a notification
  }
}
</script>