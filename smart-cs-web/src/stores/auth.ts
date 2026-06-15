import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import * as api from '@/utils/api'

export const useAuthStore = defineStore(
  'auth',
  () => {
    const token = ref<string | null>(localStorage.getItem('auth_token'))
    const user = ref<User | null>(JSON.parse(localStorage.getItem('auth_user') || 'null'))
    const isReady = ref(false)

    const isAuthenticated = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')

    async function login(username: string, password: string) {
      const res = await api.login({ username, password })
      token.value = res.accessToken
      user.value = res.user
      localStorage.setItem('auth_token', res.accessToken)
      localStorage.setItem('auth_user', JSON.stringify(res.user))
    }

    async function register(username: string, password: string, displayName: string) {
      const res = await api.register({ username, password, displayName })
      token.value = res.accessToken
      user.value = res.user
      localStorage.setItem('auth_token', res.accessToken)
      localStorage.setItem('auth_user', JSON.stringify(res.user))
    }

    async function verifyToken() {
      if (!token.value) {
        isReady.value = true
        return
      }
      try {
        const profile = await api.getMe()
        user.value = {
          id: profile.id,
          username: profile.username,
          displayName: profile.displayName,
          role: profile.role as 'user' | 'admin',
          createdAt: profile.createdAt,
        }
        localStorage.setItem('auth_user', JSON.stringify(user.value))
      } catch {
        logout()
      } finally {
        isReady.value = true
      }
    }

    function logout() {
      token.value = null
      user.value = null
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
    }

    return { token, user, isReady, isAuthenticated, isAdmin, login, register, verifyToken, logout }
  },
)
