<template>
  <div class="space-y-8">
    <div class="text-center">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">Contact Information</h2>
      <p class="text-lg text-gray-600">Please provide your contact details and address</p>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-8">
      <!-- Contact Details -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
          </svg>
          Contact Details
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label for="email" class="block text-sm font-semibold text-gray-700">Email Address *</label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.email }"
              placeholder="Enter your email address"
            />
            <p v-if="errors.email" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.email }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="phone" class="block text-sm font-semibold text-gray-700">Phone Number *</label>
            <input
              id="phone"
              v-model="formData.phone"
              type="tel"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.phone }"
              placeholder="Enter your phone number"
            />
            <p v-if="errors.phone" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.phone }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="alternative_phone" class="block text-sm font-semibold text-gray-700">Alternative Phone</label>
            <input
              id="alternative_phone"
              v-model="formData.alternative_phone"
              type="tel"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.alternative_phone }"
              placeholder="Enter alternative phone number"
            />
            <p v-if="errors.alternative_phone" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.alternative_phone }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="emergency_contact" class="block text-sm font-semibold text-gray-700">Emergency Contact *</label>
            <input
              id="emergency_contact"
              v-model="formData.emergency_contact"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.emergency_contact }"
              placeholder="Enter emergency contact name and phone"
            />
            <p v-if="errors.emergency_contact" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.emergency_contact }}
            </p>
          </div>
        </div>
      </div>

      <!-- Address Information -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          Address Information
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label for="street_address" class="block text-sm font-semibold text-gray-700">Street Address *</label>
            <input
              id="street_address"
              v-model="formData.street_address"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.street_address }"
              placeholder="Enter your street address"
            />
            <p v-if="errors.street_address" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.street_address }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="city" class="block text-sm font-semibold text-gray-700">City *</label>
            <input
              id="city"
              v-model="formData.city"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.city }"
              placeholder="Enter your city"
            />
            <p v-if="errors.city" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.city }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="state" class="block text-sm font-semibold text-gray-700">State/Province *</label>
            <input
              id="state"
              v-model="formData.state"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.state }"
              placeholder="Enter your state or province"
            />
            <p v-if="errors.state" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.state }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="postal_code" class="block text-sm font-semibold text-gray-700">Postal Code *</label>
            <input
              id="postal_code"
              v-model="formData.postal_code"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.postal_code }"
              placeholder="Enter your postal code"
            />
            <p v-if="errors.postal_code" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.postal_code }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="country" class="block text-sm font-semibold text-gray-700">Country *</label>
            <input
              id="country"
              v-model="formData.country"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.country }"
              placeholder="Enter your country"
            />
            <p v-if="errors.country" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.country }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="residence_type" class="block text-sm font-semibold text-gray-700">Residence Type *</label>
            <select
              id="residence_type"
              v-model="formData.residence_type"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.residence_type }"
            >
              <option value="">Select residence type</option>
              <option value="owned">Owned</option>
              <option value="rented">Rented</option>
              <option value="family_home">Family Home</option>
              <option value="shared">Shared Accommodation</option>
              <option value="other">Other</option>
            </select>
            <p v-if="errors.residence_type" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.residence_type }}
            </p>
          </div>
        </div>

        <div class="mt-6 space-y-2">
          <label for="time_at_address" class="block text-sm font-semibold text-gray-700">Time at Current Address *</label>
          <select
            id="time_at_address"
            v-model="formData.time_at_address"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
            :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.time_at_address }"
          >
            <option value="">Select time period</option>
            <option value="less_than_1_year">Less than 1 year</option>
            <option value="1_to_2_years">1-2 years</option>
            <option value="2_to_5_years">2-5 years</option>
            <option value="5_to_10_years">5-10 years</option>
            <option value="more_than_10_years">More than 10 years</option>
          </select>
          <p v-if="errors.time_at_address" class="text-sm text-red-600 flex items-center">
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            {{ errors.time_at_address }}
          </p>
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
            Next
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
  }
})

const emit = defineEmits(['next', 'previous', 'update-data'])

const isSubmitting = ref(false)
const errors = reactive({})

const formData = reactive({
  email: '',
  phone: '',
  alternative_phone: '',
  emergency_contact: '',
  street_address: '',
  city: '',
  state: '',
  postal_code: '',
  country: '',
  residence_type: '',
  time_at_address: ''
})

onMounted(() => {
  // Load existing data if available
  if (props.stepData && Object.keys(props.stepData).length > 0) {
    Object.assign(formData, props.stepData)
  }
})

const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const validatePhone = (phone) => {
  const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/
  return phoneRegex.test(phone.replace(/\s/g, ''))
}

const validateForm = () => {
  errors.value = {}
  
  if (!formData.email?.trim()) {
    errors.email = 'Email is required'
  } else if (!validateEmail(formData.email)) {
    errors.email = 'Please enter a valid email address'
  }
  
  if (!formData.phone?.trim()) {
    errors.phone = 'Phone number is required'
  } else if (!validatePhone(formData.phone)) {
    errors.phone = 'Please enter a valid phone number'
  }
  
  if (formData.alternative_phone && !validatePhone(formData.alternative_phone)) {
    errors.alternative_phone = 'Please enter a valid phone number'
  }
  
  if (!formData.emergency_contact?.trim()) {
    errors.emergency_contact = 'Emergency contact is required'
  }
  
  if (!formData.street_address?.trim()) {
    errors.street_address = 'Street address is required'
  }
  
  if (!formData.city?.trim()) {
    errors.city = 'City is required'
  }
  
  if (!formData.state?.trim()) {
    errors.state = 'State/Province is required'
  }
  
  if (!formData.postal_code?.trim()) {
    errors.postal_code = 'Postal code is required'
  }
  
  if (!formData.country?.trim()) {
    errors.country = 'Country is required'
  }
  
  if (!formData.residence_type) {
    errors.residence_type = 'Residence type is required'
  }
  
  if (!formData.time_at_address) {
    errors.time_at_address = 'Time at current address is required'
  }
  
  return Object.keys(errors.value).length === 0
}

const handleSubmit = async () => {
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