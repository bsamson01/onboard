import api from './api'

export const loanService = {
  // Eligibility checking
  async checkEligibility(applicationId) {
    let url = '/loans/eligibility-check'
    if (applicationId) {
      url += `?application_id=${applicationId}`
    }
    const response = await api.post(url)
    return response.data
  },

  // Loan application CRUD operations
  async createLoanApplication(data) {
    const response = await api.post('/loans/applications', data)
    return response.data
  },
  
  async getLoanApplications(params = {}) {
    const queryParams = new URLSearchParams()
    
    if (params.page) queryParams.append('page', params.page)
    if (params.size) queryParams.append('size', params.size)
    if (params.status) queryParams.append('status', params.status)
    
    const queryString = queryParams.toString()
    const url = `/loans/applications${queryString ? `?${queryString}` : ''}`
    
    const response = await api.get(url)
    return response.data
  },
  
  async getLoanApplication(id) {
    const response = await api.get(`/loans/applications/${id}`)
    return response.data
  },
  
  async updateLoanApplication(id, data) {
    const response = await api.put(`/loans/applications/${id}`, data)
    return response.data
  },
  
  async submitLoanApplication(id, confirmSubmission = true) {
    const response = await api.post(`/loans/applications/${id}/submit`, {
      confirm_submission: confirmSubmission
    })
    return response.data
  },
  
  async cancelLoanApplication(id) {
    const response = await api.delete(`/loans/applications/${id}`)
    return response.data
  },

  // Status and credit score
  async getApplicationStatus(id) {
    const response = await api.get(`/loans/applications/${id}/status`)
    return response.data
  },
  
  async getCreditScore(id) {
    const response = await api.get(`/loans/applications/${id}/credit-score`)
    return response.data
  },

  // Admin endpoints
  async getAllLoanApplications(params = {}) {
    const queryParams = new URLSearchParams()
    
    if (params.page) queryParams.append('page', params.page)
    if (params.size) queryParams.append('size', params.size)
    if (params.status) queryParams.append('status', params.status)
    if (params.assigned_officer_id) queryParams.append('assigned_officer_id', params.assigned_officer_id)
    
    const queryString = queryParams.toString()
    const url = `/loans/admin/applications${queryString ? `?${queryString}` : ''}`
    
    const response = await api.get(url)
    return response.data
  },
  
  async createLoanDecision(applicationId, decisionData) {
    const response = await api.post(`/loans/admin/applications/${applicationId}/decisions`, decisionData)
    return response.data
  },

  // Utility functions
  formatLoanType(loanType) {
    const types = {
      'personal': 'Personal Loan',
      'business': 'Business Loan',
      'emergency': 'Emergency Loan',
      'education': 'Education Loan',
      'agriculture': 'Agriculture Loan',
      'microenterprise': 'Microenterprise Loan'
    }
    return types[loanType] || loanType
  },
  
  formatStatus(status) {
    const statuses = {
      'in_progress': 'In Progress',
      'submitted': 'Submitted',
      'under_review': 'Under Review',
      'approved': 'Approved',
      'rejected': 'Rejected',
      'cancelled': 'Cancelled',
      'awaiting_disbursement': 'Awaiting Disbursement',
      'done': 'Completed'
    }
    return statuses[status] || status
  },
  
  getStatusColor(status) {
    const colors = {
      'in_progress': 'blue',
      'submitted': 'yellow',
      'under_review': 'orange',
      'approved': 'green',
      'rejected': 'red',
      'cancelled': 'gray',
      'awaiting_disbursement': 'purple',
      'done': 'green'
    }
    return colors[status] || 'gray'
  },
  
  formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  },
  
  calculateMonthlyPayment(principal, annualRate, termMonths) {
    if (annualRate === 0) return principal / termMonths
    
    const monthlyRate = annualRate / 100 / 12
    const payment = principal * (monthlyRate * Math.pow(1 + monthlyRate, termMonths)) / 
                   (Math.pow(1 + monthlyRate, termMonths) - 1)
    
    return payment
  },
  
  validateLoanApplication(data) {
    const errors = []
    
    if (!data.loan_type) {
      errors.push('Loan type is required')
    }
    
    if (!data.requested_amount || data.requested_amount <= 0) {
      errors.push('Requested amount must be greater than 0')
    }
    
    if (data.requested_amount > 1000000) {
      errors.push('Requested amount cannot exceed $1,000,000')
    }
    
    if (!data.loan_purpose || data.loan_purpose.trim().length < 10) {
      errors.push('Loan purpose must be at least 10 characters')
    }
    
    if (!data.repayment_period_months || data.repayment_period_months < 6 || data.repayment_period_months > 60) {
      errors.push('Repayment period must be between 6 and 60 months')
    }
    
    return errors
  },
  
  getLoanTypeOptions() {
    return [
      { value: 'personal', label: 'Personal Loan', description: 'For personal expenses and needs' },
      { value: 'business', label: 'Business Loan', description: 'For business operations and growth' },
      { value: 'emergency', label: 'Emergency Loan', description: 'For urgent financial needs' },
      { value: 'education', label: 'Education Loan', description: 'For educational expenses' },
      { value: 'agriculture', label: 'Agriculture Loan', description: 'For farming and agricultural activities' },
      { value: 'microenterprise', label: 'Microenterprise Loan', description: 'For small business ventures' }
    ]
  },
  
  getRepaymentTermOptions() {
    return [
      { value: 6, label: '6 months', description: 'Short term' },
      { value: 12, label: '1 year', description: 'Standard term' },
      { value: 18, label: '18 months', description: 'Medium term' },
      { value: 24, label: '2 years', description: 'Extended term' },
      { value: 36, label: '3 years', description: 'Long term' },
      { value: 48, label: '4 years', description: 'Extended long term' },
      { value: 60, label: '5 years', description: 'Maximum term' }
    ]
  },
  
  // Error handling
  handleApiError(error) {
    if (error.response?.data?.detail) {
      return error.response.data.detail
    }
    
    if (error.response?.status === 400) {
      return 'Invalid request. Please check your input and try again.'
    }
    
    if (error.response?.status === 401) {
      return 'You are not authorized. Please log in and try again.'
    }
    
    if (error.response?.status === 403) {
      return 'You do not have permission to perform this action.'
    }
    
    if (error.response?.status === 404) {
      return 'The requested loan application was not found.'
    }
    
    if (error.response?.status >= 500) {
      return 'Server error. Please try again later.'
    }
    
    return 'An unexpected error occurred. Please try again.'
  }
}