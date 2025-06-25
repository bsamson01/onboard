import api from './api'

export const onboardingService = {
  // Create new onboarding application
  createApplication: () => api.post('/onboarding/applications'),
  
  // Get user's onboarding applications
  getApplications: () => api.get('/onboarding/applications'),
  
  // Get specific application
  getApplication: (applicationId) => api.get(`/onboarding/applications/${applicationId}`),
  
  // Complete a step
  completeStep: (applicationId, stepNumber, stepData) => 
    api.post(`/onboarding/applications/${applicationId}/steps/${stepNumber}`, {
      step_number: stepNumber,
      step_data: stepData
    }),
  
  // Upload document
  uploadDocument: (applicationId, documentType, file) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)
    
    return api.post(`/onboarding/applications/${applicationId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // Submit application
  submitApplication: (applicationId) => 
    api.post(`/onboarding/applications/${applicationId}/submit`),
  
  // Get progress
  getProgress: (applicationId) => 
    api.get(`/onboarding/applications/${applicationId}/progress`)
}