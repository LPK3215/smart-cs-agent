import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  // ===== 用户端 =====
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
    meta: { requiresAuth: true, layout: 'user' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true, layout: 'user' },
  },

  // ===== 管理端 =====
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/AdminLoginView.vue'),
    meta: { requiresAuth: false, layout: 'blank' },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, layout: 'admin' },
  },

  // Catch-all
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

  if (!authStore.isReady) {
    await authStore.verifyToken()
  }

  const isAdminRoute = to.path.startsWith('/admin')

  // 未登录 → 跳转到对应的登录页
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    return isAdminRoute ? { name: 'AdminLogin' } : { name: 'Login' }
  }

  // 需要管理员权限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: 'Chat' }
  }

  // 已登录访问登录页 → 跳转到首页
  if ((to.name === 'Login' || to.name === 'AdminLogin') && authStore.isAuthenticated) {
    return authStore.isAdmin ? { name: 'Admin' } : { name: 'Chat' }
  }

  // 管理员登录后访问用户端 → 重定向到管理后台（管理员不需要用户聊天功能）
  if (!isAdminRoute && to.meta.requiresAuth && authStore.isAdmin && to.name !== 'Profile') {
    return { name: 'Admin' }
  }

  // 普通用户尝试访问管理端 → 跳回聊天页
  if (isAdminRoute && to.meta.requiresAuth && !authStore.isAdmin) {
    return { name: 'Chat' }
  }
})

export default router
