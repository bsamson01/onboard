<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">

    <!-- Hero Section -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20 animate__animated animate__fadeInUp">
      <div class="text-center">
        <h1 class="text-5xl font-extrabold text-gray-900 sm:text-6xl md:text-7xl animate__animated animate__fadeInDown animate__delay-1s">
          Your Financial Journey <span class="text-blue-600 animate__animated animate__heartBeat animate__delay-2s">Starts Here</span>
        </h1>
        <p class="mt-5 max-w-2xl mx-auto text-lg text-gray-600 animate__animated animate__fadeIn animate__delay-1s">
          Complete our streamlined onboarding process to access personalized microfinance solutions tailored to your needs.
        </p>
        <div class="mt-8 flex justify-center animate__animated animate__fadeInUp animate__delay-2s">
          <button
            @click="router.push('/signup')"
            class="px-10 py-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xl font-semibold shadow-lg transition-all"
          >
            Get Started
          </button>
        </div>
      </div>
    </div>

    <!-- About Section -->
    <section class="py-16 bg-white animate__animated animate__fadeInUp animate__delay-1s">
      <div class="max-w-5xl mx-auto px-4 text-center">
        <h2 class="text-3xl font-bold text-blue-700 mb-4">About Us</h2>
        <p class="text-lg text-gray-700 mb-6">
          We empower individuals and small businesses by providing fast, secure, and transparent access to microfinance. Our platform leverages modern technology to simplify onboarding, credit scoring, and loan management, making financial inclusion a reality for everyone.
        </p>
      </div>
    </section>

    <!-- How It Works Section -->
    <section class="py-16 bg-gradient-to-r from-blue-50 to-indigo-100 animate__animated animate__fadeInUp animate__delay-2s">
      <div class="max-w-6xl mx-auto px-4">
        <h2 class="text-3xl font-bold text-center text-blue-700 mb-10">How It Works</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div class="bg-white rounded-lg shadow p-6 text-center animate__animated animate__zoomIn animate__delay-1s">
            <div class="mb-4">
              <i class="fas fa-user-plus text-3xl text-blue-500"></i>
            </div>
            <h3 class="font-semibold text-lg mb-2">Sign Up</h3>
            <p class="text-gray-600">Create your account in minutes and start your financial journey.</p>
          </div>
          <div class="bg-white rounded-lg shadow p-6 text-center animate__animated animate__zoomIn animate__delay-2s">
            <div class="mb-4">
              <i class="fas fa-id-card text-3xl text-indigo-500"></i>
            </div>
            <h3 class="font-semibold text-lg mb-2">Complete Onboarding</h3>
            <p class="text-gray-600">Fill in your details, upload documents, and get verified instantly.</p>
          </div>
          <div class="bg-white rounded-lg shadow p-6 text-center animate__animated animate__zoomIn animate__delay-3s">
            <div class="mb-4">
              <i class="fas fa-chart-line text-3xl text-green-500"></i>
            </div>
            <h3 class="font-semibold text-lg mb-2">Get Scored</h3>
            <p class="text-gray-600">Receive a transparent credit score and personalized recommendations.</p>
          </div>
          <div class="bg-white rounded-lg shadow p-6 text-center animate__animated animate__zoomIn animate__delay-4s">
            <div class="mb-4">
              <i class="fas fa-hand-holding-usd text-3xl text-yellow-500"></i>
            </div>
            <h3 class="font-semibold text-lg mb-2">Access Loans</h3>
            <p class="text-gray-600">Apply for loans and manage your finances with ease and security.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section (animated) -->
    <div class="py-16 bg-white animate__animated animate__fadeInUp animate__delay-3s">
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
            <div class="flex flex-col items-center text-center animate__animated animate__fadeInUp animate__delay-1s">
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
            <div class="flex flex-col items-center text-center animate__animated animate__fadeInUp animate__delay-2s">
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
            <div class="flex flex-col items-center text-center animate__animated animate__fadeInUp animate__delay-3s">
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

    <!-- Testimonials Section -->
    <section class="py-16 bg-gradient-to-r from-indigo-50 to-blue-100 animate__animated animate__fadeInUp animate__delay-4s">
      <div class="max-w-5xl mx-auto px-4">
        <h2 class="text-3xl font-bold text-center text-blue-700 mb-10">What Our Customers Say</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="bg-white rounded-lg shadow p-6 animate__animated animate__fadeIn animate__delay-1s">
            <p class="text-gray-700 italic mb-4">"The onboarding was so easy and fast. I got my loan approved in days!"</p>
            <div class="flex items-center justify-center">
              <span class="font-bold text-blue-700">Amina K.</span>
            </div>
          </div>
          <div class="bg-white rounded-lg shadow p-6 animate__animated animate__fadeIn animate__delay-2s">
            <p class="text-gray-700 italic mb-4">"I love the transparency and the support team is amazing."</p>
            <div class="flex items-center justify-center">
              <span class="font-bold text-blue-700">Samuel O.</span>
            </div>
          </div>
          <div class="bg-white rounded-lg shadow p-6 animate__animated animate__fadeIn animate__delay-3s">
            <p class="text-gray-700 italic mb-4">"The best microfinance experience I've ever had. Highly recommended!"</p>
            <div class="flex items-center justify-center">
              <span class="font-bold text-blue-700">Grace M.</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- FAQ Section -->
    <section class="py-16 bg-white animate__animated animate__fadeInUp animate__delay-5s">
      <div class="max-w-4xl mx-auto px-4">
        <h2 class="text-3xl font-bold text-center text-blue-700 mb-10">Frequently Asked Questions</h2>
        <div class="space-y-6">
          <div class="bg-blue-50 rounded-lg p-6 shadow animate__animated animate__fadeIn animate__delay-1s">
            <h3 class="font-semibold text-lg mb-2">Who can sign up?</h3>
            <p class="text-gray-700">Any individual or small business seeking microfinance solutions can sign up as a customer.</p>
          </div>
          <div class="bg-blue-50 rounded-lg p-6 shadow animate__animated animate__fadeIn animate__delay-2s">
            <h3 class="font-semibold text-lg mb-2">Is my data secure?</h3>
            <p class="text-gray-700">Absolutely. We use industry-standard encryption and maintain full audit trails for transparency and security.</p>
          </div>
          <div class="bg-blue-50 rounded-lg p-6 shadow animate__animated animate__fadeIn animate__delay-3s">
            <h3 class="font-semibold text-lg mb-2">How long does onboarding take?</h3>
            <p class="text-gray-700">Most customers complete onboarding and get a decision within a few days.</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import 'animate.css'

const router = useRouter()
const authStore = useAuthStore()

onMounted(() => {
  // Redirect authenticated users to dashboard
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
.btn-primary {
  @apply bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded shadow transition-all;
}
.btn-secondary {
  @apply bg-white border border-blue-600 text-blue-600 font-semibold py-2 px-4 rounded shadow hover:bg-blue-50 transition-all;
}
</style>