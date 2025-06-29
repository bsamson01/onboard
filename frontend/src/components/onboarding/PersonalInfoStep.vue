<template>
  <div class="space-y-8">
    <div class="text-center">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">Personal Information</h2>
      <p class="text-lg text-gray-600">Please provide your basic personal details</p>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-8">
      <!-- Personal Details -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
          </svg>
          Personal Details
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label for="first_name" class="block text-sm font-semibold text-gray-700">First Name *</label>
            <input
              id="first_name"
              v-model="formData.first_name"
              type="text"
              required
              :disabled="isReadOnly"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 
                'border-red-300 focus:ring-red-500 focus:border-red-500': errors.first_name,
                'bg-gray-100 cursor-not-allowed': isReadOnly
              }"
              placeholder="Enter your first name"
            />
            <p v-if="errors.first_name" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.first_name }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="last_name" class="block text-sm font-semibold text-gray-700">Last Name *</label>
            <input
              id="last_name"
              v-model="formData.last_name"
              type="text"
              required
              :disabled="isReadOnly"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 
                'border-red-300 focus:ring-red-500 focus:border-red-500': errors.last_name,
                'bg-gray-100 cursor-not-allowed': isReadOnly
              }"
              placeholder="Enter your last name"
            />
            <p v-if="errors.last_name" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.last_name }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="date_of_birth" class="block text-sm font-semibold text-gray-700">Date of Birth *</label>
            <input
              id="date_of_birth"
              v-model="formData.date_of_birth"
              type="date"
              required
              :disabled="isReadOnly"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 
                'border-red-300 focus:ring-red-500 focus:border-red-500': errors.date_of_birth,
                'bg-gray-100 cursor-not-allowed': isReadOnly
              }"
            />
            <p v-if="errors.date_of_birth" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.date_of_birth }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="gender" class="block text-sm font-semibold text-gray-700">Gender *</label>
            <select
              id="gender"
              v-model="formData.gender"
              required
              :disabled="isReadOnly"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 
                'border-red-300 focus:ring-red-500 focus:border-red-500': errors.gender,
                'bg-gray-100 cursor-not-allowed': isReadOnly
              }"
            >
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </select>
            <p v-if="errors.gender" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.gender }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="nationality" class="block text-sm font-semibold text-gray-700">Nationality *</label>
            <input
              id="nationality"
              v-model="formData.nationality"
              type="text"
              required
              :disabled="isReadOnly"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 
                'border-red-300 focus:ring-red-500 focus:border-red-500': errors.nationality,
                'bg-gray-100 cursor-not-allowed': isReadOnly
              }"
              placeholder="Enter your nationality"
            />
            <p v-if="errors.nationality" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.nationality }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="id_number" class="block text-sm font-semibold text-gray-700">ID Number *</label>
            <input
              id="id_number"
              v-model="formData.id_number"
              type="text"
              required
              :disabled="isReadOnly"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 
                'border-red-300 focus:ring-red-500 focus:border-red-500': errors.id_number,
                'bg-gray-100 cursor-not-allowed': isReadOnly
              }"
              placeholder="Enter your ID number"
            />
            <p v-if="errors.id_number" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.id_number }}
            </p>
          </div>
        </div>
      </div>

      <!-- Additional Information -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
          </svg>
          Additional Information
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label for="marital_status" class="block text-sm font-semibold text-gray-700">Marital Status *</label>
            <select
              id="marital_status"
              v-model="formData.marital_status"
              required
              :disabled="isReadOnly"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 
                'border-red-300 focus:ring-red-500 focus:border-red-500': errors.marital_status,
                'bg-gray-100 cursor-not-allowed': isReadOnly
              }"
            >
              <option value="">Select marital status</option>
              <option value="single">Single</option>
              <option value="married">Married</option>
              <option value="divorced">Divorced</option>
              <option value="widowed">Widowed</option>
              <option value="separated">Separated</option>
            </select>
            <p v-if="errors.marital_status" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.marital_status }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="dependents" class="block text-sm font-semibold text-gray-700">Number of Dependents</label>
            <input
              id="dependents"
              v-model.number="formData.dependents"
              type="number"
              min="0"
              max="20"
              :disabled="isReadOnly"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 
                'border-red-300 focus:ring-red-500 focus:border-red-500': errors.dependents,
                'bg-gray-100 cursor-not-allowed': isReadOnly
              }"
              placeholder="0"
            />
            <p v-if="errors.dependents" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.dependents }}
            </p>
          </div>
        </div>
      </div>

      <!-- Navigation Buttons -->
      <div class="flex justify-between pt-8">
        <button
          type="button"
          @click="$emit('previous')"
          class="px-6 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200"
        >
          <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
          </svg>
          Previous
        </button>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="px-6 py-3 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          <span v-if="isSubmitting" class="flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Saving...
          </span>
          <span v-else class="flex items-center">
            {{ isReadOnly ? 'Next' : 'Next' }}
            <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const props = defineProps({
  application: {
    type: Object,
    default: null
  },
  stepData: {
    type: Object,
    default: () => ({})
  },
  isReadOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['next', 'previous', 'update-data'])

const isSubmitting = ref(false)
const errors = reactive({})

const formData = reactive({
  first_name: '',
  last_name: '',
  date_of_birth: '',
  gender: '',
  nationality: '',
  id_number: '',
  marital_status: '',
  dependents: 0
})

onMounted(() => {
  // Load existing data if available
  if (props.stepData && Object.keys(props.stepData).length > 0) {
    const data = { ...props.stepData }
    
    // Ensure numeric fields are properly converted
    if (data.dependents !== undefined) {
      formData.dependents = Number(data.dependents) || 0
    }
    
    // Handle other fields
    Object.keys(data).forEach(key => {
      if (key !== 'dependents') {
        formData[key] = data[key]
      }
    })
  }
})

const validateForm = () => {
  errors.value = {}
  
  if (!formData.first_name?.trim()) {
    errors.first_name = 'First name is required'
  }
  
  if (!formData.last_name?.trim()) {
    errors.last_name = 'Last name is required'
  }
  
  if (!formData.date_of_birth) {
    errors.date_of_birth = 'Date of birth is required'
  } else {
    const today = new Date()
    const birthDate = new Date(formData.date_of_birth)
    const age = today.getFullYear() - birthDate.getFullYear()
    if (age < 18) {
      errors.date_of_birth = 'You must be at least 18 years old'
    }
  }
  
  if (!formData.gender) {
    errors.gender = 'Gender is required'
  }
  
  if (!formData.nationality?.trim()) {
    errors.nationality = 'Nationality is required'
  }
  
  if (!formData.id_number?.trim()) {
    errors.id_number = 'ID number is required'
  }
  
  if (!formData.marital_status) {
    errors.marital_status = 'Marital status is required'
  }
  
  if (formData.dependents < 0) {
    errors.dependents = 'Number of dependents cannot be negative'
  }
  
  return Object.keys(errors.value).length === 0
}

const handleSubmit = async () => {
  if (isReadOnly) {
    // In read-only mode, just navigate to next step without validation or submission
    emit('next', { ...formData })
    return
  }
  
  if (!validateForm()) {
    return
  }
  
  isSubmitting.value = true
  
  try {
    emit('next', { ...formData })
  } catch (error) {
    console.error('Error submitting form:', error)
  } finally {
    isSubmitting.value = false
  }
}
</script> 