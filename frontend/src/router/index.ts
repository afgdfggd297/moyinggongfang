import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/Home.vue'),
    },
    {
      path: '/create',
      name: 'create',
      component: () => import('../views/Create.vue'),
    },
    {
      path: '/create-docx',
      name: 'create-docx',
      component: () => import('../views/CreateDocx.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/templates',
      name: 'templates',
      component: () => import('../views/Templates.vue'),
    },
  ],
})

// Navigation guard — protect routes that require authentication
let authInitialized = false

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // On first navigation, restore auth state from localStorage token
  if (!authInitialized) {
    authInitialized = true
    await auth.checkAuth()
  }

  // If route requires auth and user is not authenticated, redirect to login
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})

export default router
