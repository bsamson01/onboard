import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import OnboardingWizard from '@/views/OnboardingWizard.vue'
import CustomerDashboard from '@/views/CustomerDashboard.vue'
import AdminDashboard from '@/views/AdminDashboard.vue'
import ApplicationReviewPanel from '@/components/admin/ApplicationReviewPanel.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/dashboard',
    name: 'CustomerDashboard',
    component: CustomerDashboard,
    meta: { requiresAuth: true, roles: ['customer'] }
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, roles: ['admin', 'loan_officer', 'risk_officer'] }
  },
  {
    path: '/applications',
    name: 'ApplicationReview',
    component: ApplicationReviewPanel,
    meta: { requiresAuth: true, roles: ['admin', 'loan_officer', 'risk_officer'] }
  },
  {
    path: '/onboarding',
    name: 'OnboardingWizard',
    component: OnboardingWizard,
    meta: { requiresAuth: true, roles: ['customer'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication and role-based access
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const userRole = authStore.user?.role

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.roles && authStore.isAuthenticated) {
    if (to.meta.roles.includes(userRole)) {
      next()
    } else {
      // Only redirect if not already on the correct dashboard
      if ((userRole === 'admin' || userRole === 'loan_officer' || userRole === 'risk_officer') && to.path !== '/admin') {
        next('/admin')
      } else if (userRole === 'customer' && to.path !== '/dashboard') {
        next('/dashboard')
      } else {
        // Prevent infinite loop by aborting navigation
        next(false)
      }
    }
  } else {
    next()
  }
})

export default router