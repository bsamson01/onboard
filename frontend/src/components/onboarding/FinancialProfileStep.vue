<template>
  <div class="space-y-8">
    <div class="text-center">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">Financial Profile</h2>
      <p class="text-lg text-gray-600">Please provide your employment and financial information</p>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-8">
      <!-- Employment Information -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
          </svg>
          Employment Information
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label for="employment_status" class="block text-sm font-semibold text-gray-700">Employment Status *</label>
            <select
              id="employment_status"
              v-model="formData.employment_status"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.employment_status }"
            >
              <option value="">Select employment status</option>
              <option value="employed">Employed</option>
              <option value="self_employed">Self-Employed</option>
              <option value="unemployed">Unemployed</option>
              <option value="student">Student</option>
              <option value="retired">Retired</option>
              <option value="other">Other</option>
            </select>
            <p v-if="errors.employment_status" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.employment_status }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="employer_name" class="block text-sm font-semibold text-gray-700">Employer Name</label>
            <input
              id="employer_name"
              v-model="formData.employer_name"
              type="text"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.employer_name }"
              placeholder="Enter your employer's name"
            />
            <p v-if="errors.employer_name" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.employer_name }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="job_title" class="block text-sm font-semibold text-gray-700">Job Title</label>
            <input
              id="job_title"
              v-model="formData.job_title"
              type="text"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.job_title }"
              placeholder="Enter your job title"
            />
            <p v-if="errors.job_title" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.job_title }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="employment_duration_months" class="block text-sm font-semibold text-gray-700">Employment Duration</label>
            <select
              id="employment_duration_months"
              v-model="formData.employment_duration_months"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.employment_duration_months }"
            >
              <option value="">Select duration</option>
              <option value="less_than_1_year">Less than 1 year</option>
              <option value="1_to_2_years">1-2 years</option>
              <option value="2_to_5_years">2-5 years</option>
              <option value="5_to_10_years">5-10 years</option>
              <option value="more_than_10_years">More than 10 years</option>
            </select>
            <p v-if="errors.employment_duration_months" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.employment_duration_months }}
            </p>
          </div>
        </div>
      </div>

      <!-- Income Information -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
          </svg>
          Income Information
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label for="monthly_income" class="block text-sm font-semibold text-gray-700">Monthly Income *</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <span class="text-gray-500 text-lg font-medium">$</span>
              </div>
              <input
                id="monthly_income"
                v-model.number="formData.monthly_income"
                type="number"
                min="0"
                step="0.01"
                required
                class="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
                :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.monthly_income }"
                placeholder="0.00"
              />
            </div>
            <p v-if="errors.monthly_income" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.monthly_income }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="income_source" class="block text-sm font-semibold text-gray-700">Primary Income Source *</label>
            <select
              id="income_source"
              v-model="formData.income_source"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.income_source }"
            >
              <option value="">Select income source</option>
              <option value="salary">Salary/Wages</option>
              <option value="business">Business Income</option>
              <option value="investments">Investments</option>
              <option value="pension">Pension</option>
              <option value="government_benefits">Government Benefits</option>
              <option value="other">Other</option>
            </select>
            <p v-if="errors.income_source" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.income_source }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="additional_income" class="block text-sm font-semibold text-gray-700">Additional Monthly Income</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <span class="text-gray-500 text-lg font-medium">$</span>
              </div>
              <input
                id="additional_income"
                v-model.number="formData.additional_income"
                type="number"
                min="0"
                step="0.01"
                class="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
                :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.additional_income }"
                placeholder="0.00"
              />
            </div>
            <p v-if="errors.additional_income" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.additional_income }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="income_frequency" class="block text-sm font-semibold text-gray-700">Income Frequency *</label>
            <select
              id="income_frequency"
              v-model="formData.income_frequency"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.income_frequency }"
            >
              <option value="">Select frequency</option>
              <option value="weekly">Weekly</option>
              <option value="biweekly">Bi-weekly</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="annually">Annually</option>
            </select>
            <p v-if="errors.income_frequency" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.income_frequency }}
            </p>
          </div>
        </div>
      </div>

      <!-- Financial Information -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <svg class="w-6 h-6 mr-3 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
          </svg>
          Financial Information
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label for="monthly_expenses" class="block text-sm font-semibold text-gray-700">Monthly Expenses *</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <span class="text-gray-500 text-lg font-medium">$</span>
              </div>
              <input
                id="monthly_expenses"
                v-model.number="formData.monthly_expenses"
                type="number"
                min="0"
                step="0.01"
                required
                class="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
                :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.monthly_expenses }"
                placeholder="0.00"
              />
            </div>
            <p v-if="errors.monthly_expenses" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.monthly_expenses }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="existing_loans" class="block text-sm font-semibold text-gray-700">Existing Loans/Mortgages</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <span class="text-gray-500 text-lg font-medium">$</span>
              </div>
              <input
                id="existing_loans"
                v-model.number="formData.existing_loans"
                type="number"
                min="0"
                step="0.01"
                class="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
                :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.existing_loans }"
                placeholder="0.00"
              />
            </div>
            <p v-if="errors.existing_loans" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.existing_loans }}
            </p>
          </div>

          <div class="space-y-2">
            <label for="number_of_bank_accounts" class="block text-sm font-semibold text-gray-700">Number of Bank Accounts</label>
            <input
              id="number_of_bank_accounts"
              v-model.number="formData.number_of_bank_accounts"
              type="number"
              min="0"
              max="10"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.number_of_bank_accounts }"
              placeholder="0"
            />
            <p v-if="errors.number_of_bank_accounts" class="text-sm text-red-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ errors.number_of_bank_accounts }}
            </p>
          </div>
        </div>

        <!-- Bank Details (conditional) -->
        <div v-if="formData.number_of_bank_accounts > 0" class="mt-8">
          <div class="bg-blue-50 rounded-lg p-6 border border-blue-200">
            <h4 class="text-lg font-semibold text-blue-900 mb-4 flex items-center">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path>
              </svg>
              Bank Account Details
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="space-y-2">
                <label for="bank_name" class="block text-sm font-semibold text-gray-700">Bank Name *</label>
                <input
                  id="bank_name"
                  v-model="formData.bank_name"
                  type="text"
                  required
                  class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
                  :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.bank_name }"
                  placeholder="Enter bank name"
                />
                <p v-if="errors.bank_name" class="text-sm text-red-600 flex items-center">
                  <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                  {{ errors.bank_name }}
                </p>
              </div>

              <div class="space-y-2">
                <label for="bank_account_number" class="block text-sm font-semibold text-gray-700">Account Number *</label>
                <input
                  id="bank_account_number"
                  v-model="formData.bank_account_number"
                  type="text"
                  required
                  class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
                  :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.bank_account_number }"
                  placeholder="Enter account number"
                />
                <p v-if="errors.bank_account_number" class="text-sm text-red-600 flex items-center">
                  <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                  {{ errors.bank_account_number }}
                </p>
              </div>

              <div class="space-y-2">
                <label for="bank_account_type" class="block text-sm font-semibold text-gray-700">Account Type</label>
                <select
                  id="bank_account_type"
                  v-model="formData.bank_account_type"
                  class="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 hover:border-gray-400"
                  :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': errors.bank_account_type }"
                >
                  <option value="">Select account type</option>
                  <option value="savings">Savings</option>
                  <option value="checking">Checking</option>
                  <option value="current">Current</option>
                  <option value="business">Business</option>
                </select>
                <p v-if="errors.bank_account_type" class="text-sm text-red-600 flex items-center">
                  <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                  {{ errors.bank_account_type }}
                </p>
              </div>
            </div>
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
  employment_status: '',
  employer_name: '',
  job_title: '',
  employment_duration_months: '',
  monthly_income: null,
  income_source: '',
  additional_income: null,
  income_frequency: '',
  monthly_expenses: null,
  existing_loans: null,
  number_of_bank_accounts: 0,
  bank_name: '',
  bank_account_number: '',
  bank_account_type: '',
  has_other_loans: false,
  other_loans_details: [],
  credit_score: ''
})

onMounted(() => {
  // Load existing data if available
  if (props.stepData && Object.keys(props.stepData).length > 0) {
    // Convert string numbers to actual numbers for numeric fields
    const data = { ...props.stepData }
    
    // Ensure numeric fields are properly converted
    if (data.monthly_income !== undefined) {
      formData.monthly_income = Number(data.monthly_income) || null
    }
    if (data.additional_income !== undefined) {
      formData.additional_income = Number(data.additional_income) || null
    }
    if (data.monthly_expenses !== undefined) {
      formData.monthly_expenses = Number(data.monthly_expenses) || null
    }
    if (data.existing_loans !== undefined) {
      formData.existing_loans = Number(data.existing_loans) || null
    }
    if (data.number_of_bank_accounts !== undefined) {
      formData.number_of_bank_accounts = Number(data.number_of_bank_accounts) || 0
    }
    if (data.employment_duration_months !== undefined) {
      formData.employment_duration_months = Number(data.employment_duration_months) || ''
    }
    
    // Handle other fields
    Object.keys(data).forEach(key => {
      if (!['monthly_income', 'additional_income', 'monthly_expenses', 'existing_loans', 'number_of_bank_accounts', 'employment_duration_months'].includes(key)) {
        formData[key] = data[key]
      }
    })
  }
})

const validateForm = () => {
  errors.value = {}
  
  if (!formData.employment_status) {
    errors.employment_status = 'Employment status is required'
  }
  
  if (formData.employment_status === 'employed' && !formData.employer_name?.trim()) {
    errors.employer_name = 'Employer name is required for employed individuals'
  }
  
  if (!formData.monthly_income || formData.monthly_income <= 0) {
    errors.monthly_income = 'Monthly income is required and must be greater than 0'
  }
  
  if (!formData.income_source) {
    errors.income_source = 'Income source is required'
  }
  
  if (!formData.income_frequency) {
    errors.income_frequency = 'Income frequency is required'
  }
  
  if (!formData.monthly_expenses || formData.monthly_expenses < 0) {
    errors.monthly_expenses = 'Monthly expenses are required and cannot be negative'
  }
  
  if (formData.existing_loans && formData.existing_loans < 0) {
    errors.existing_loans = 'Existing loans cannot be negative'
  }
  
  if (formData.number_of_bank_accounts < 0) {
    errors.number_of_bank_accounts = 'Number of bank accounts cannot be negative'
  }
  
  // Conditional validation for bank details
  if (formData.number_of_bank_accounts > 0) {
    if (!formData.bank_name?.trim()) {
      errors.bank_name = 'Bank name is required when you have bank accounts'
    }
    if (!formData.bank_account_number?.trim()) {
      errors.bank_account_number = 'Bank account number is required when you have bank accounts'
    }
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