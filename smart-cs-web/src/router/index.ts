import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false, layout: 'blank' },
  },
  {
    path: '/',
    redirect: '/chat',
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/chat',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from) => {
  const authStore = useAuthStore()

  // Wait for initial token verification on first load
  if (!authStore.isReady) {
    await authStore.verifyToken()
  }

  // If route requires auth and user is not authenticated
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    return { name: 'Login' }
  }

  // If route requires admin and user is not admin
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: 'Chat' }
  }

  // If already logged in and trying to access login page
  if (to.name === 'Login' && authStore.isAuthenticated) {
    return { name: 'Chat' }
  }
})

export default router
