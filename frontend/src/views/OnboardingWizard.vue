<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-semibold text-gray-900">
              {{ isCompleted ? 'Application Complete' : 'Application Onboarding' }}
            </h1>
            <span v-if="application && !isCompleted" class="ml-4 text-sm text-gray-500">
              #{{ application.application_number }}
            </span>
          </div>
          <button 
            v-if="!isCompleted"
            @click="router.push('/')" 
            class="text-gray-600 hover:text-gray-900"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <!-- Progress Bar - Only show when not completed -->
      <div v-if="!isCompleted" class="mb-8">
        <div class="flex items-center justify-between">
          <div v-for="step in steps" :key="step.number" class="flex flex-col items-center">
            <div
              class="progress-step"
              :class="{
                'completed': step.number < currentStep || isStepCompleted(step.number),
                'current': step.number === currentStep,
                'pending': step.number > currentStep && !isStepCompleted(step.number)
              }"
            >
              <svg v-if="step.number < currentStep || isStepCompleted(step.number)" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              <span v-else>{{ step.number }}</span>
            </div>
            <div class="mt-2 text-center">
              <p class="text-sm font-medium text-gray-900">{{ step.name }}</p>
              <p class="text-xs text-gray-500">{{ step.description }}</p>
            </div>
          </div>
        </div>
        <!-- Progress Line -->
        <div class="mt-4 relative">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-200"></div>
          </div>
          <div class="relative flex justify-between">
            <div
              v-for="step in steps"
              :key="step.number"
              class="bg-gray-50 w-8 h-1"
              :class="{
                'bg-green-500': step.number < currentStep || isStepCompleted(step.number),
                'bg-blue-500': step.number === currentStep,
                'bg-gray-200': step.number > currentStep && !isStepCompleted(step.number)
              }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Step Content -->
      <div class="card">
        <component
          :is="currentStepComponent"
          :application="application"
          :step-data="getCurrentStepData()"
          @next="handleNext"
          @previous="handlePrevious"
          @update-data="handleDataUpdate"
        />
      </div>

      <!-- Error Display -->
      <div v-if="error" class="mt-4 rounded-md bg-red-50 p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Error</h3>
            <p class="mt-1 text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { onboardingService } from '@/services/onboarding'

// Step Components
import PersonalInfoStep from '@/components/onboarding/PersonalInfoStep.vue'
import ContactInfoStep from '@/components/onboarding/ContactInfoStep.vue'
import FinancialProfileStep from '@/components/onboarding/FinancialProfileStep.vue'
import DocumentUploadStep from '@/components/onboarding/DocumentUploadStep.vue'
import ConsentScoringStep from '@/components/onboarding/ConsentScoringStep.vue'
import ApplicationCompleteStep from '@/components/onboarding/ApplicationCompleteStep.vue'

const route = useRoute()
const router = useRouter()

const application = ref(null)
const currentStep = ref(1)
const error = ref('')
const isLoading = ref(false)
const stepData = reactive({})
const isCompleted = ref(false)

const steps = [
  { number: 1, name: 'Personal Info', description: 'Basic details', component: 'PersonalInfoStep' },
  { number: 2, name: 'Contact Info', description: 'Address & contacts', component: 'ContactInfoStep' },
  { number: 3, name: 'Financial Profile', description: 'Income & employment', component: 'FinancialProfileStep' },
  { number: 4, name: 'Documents', description: 'Upload ID docs', component: 'DocumentUploadStep' },
  { number: 5, name: 'Review & Score', description: 'Consent & scoring', component: 'ConsentScoringStep' }
]

const stepComponents = {
  PersonalInfoStep,
  ContactInfoStep,
  FinancialProfileStep,
  DocumentUploadStep,
  ConsentScoringStep,
  ApplicationCompleteStep
}

const currentStepComponent = computed(() => {
  if (isCompleted.value) {
    return ApplicationCompleteStep
  }
  const step = steps.find(s => s.number === currentStep.value)
  return stepComponents[step?.component] || PersonalInfoStep
})

const isStepCompleted = (stepNumber) => {
  if (!application.value) return false
  const step = application.value.steps.find(s => s.step_number === stepNumber)
  return step?.is_completed || false
}

const getCurrentStepData = () => {
  if (!application.value) return {}
  
  if (isCompleted.value) {
    // When completed, return step 5 data for the completion component
    const step = application.value.steps.find(s => s.step_number === 5)
    return step?.step_data || {}
  }
  
  const step = application.value.steps.find(s => s.step_number === currentStep.value)
  return step?.step_data || {}
}

const loadApplication = async () => {
  try {
    isLoading.value = true
    error.value = ''
    
    const applicationId = route.query.app
    if (!applicationId) {
      throw new Error('No application ID provided')
    }

    const response = await onboardingService.getApplication(applicationId)
    application.value = response.data
    currentStep.value = response.data.current_step
    
    // Load step data into reactive object
    response.data.steps.forEach(step => {
      if (step.step_data) {
        stepData[step.step_number] = step.step_data
      }
    })
    
  } catch (error) {
    console.error('Failed to load application:', error)
    error.value = 'Failed to load application. Please try again.'
  } finally {
    isLoading.value = false
  }
}

const handleNext = async (data) => {
  try {
    isLoading.value = true
    error.value = ''
    
    // Save current step data
    await onboardingService.completeStep(application.value.id, currentStep.value, data)
    
    // Update local step data
    stepData[currentStep.value] = data
    
    // If this is step 5 (final step), submit the application
    if (currentStep.value === 5) {
      await onboardingService.submitApplication(application.value.id)
      isCompleted.value = true
      return
    }
    
    // For steps 1-4: reload application to get updated status and move to next step
    await loadApplication()
    
  } catch (error) {
    console.error('Failed to save step:', error)
    error.value = error.response?.data?.detail || 'Failed to save step data'
  } finally {
    isLoading.value = false
  }
}

const handlePrevious = () => {
  if (currentStep.value > 1) {
    currentStep.value -= 1
  }
}

const handleDataUpdate = (data) => {
  stepData[currentStep.value] = { ...stepData[currentStep.value], ...data }
}

onMounted(() => {
  loadApplication()
})
</script>