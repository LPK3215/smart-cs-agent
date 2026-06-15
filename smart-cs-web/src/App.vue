<template>
  <!-- 用户端布局 -->
  <AppLayout v-if="route.meta.layout === 'user' && authStore.isAuthenticated">
    <router-view />
  </AppLayout>
  <!-- 管理端布局 -->
  <AdminLayout v-else-if="route.meta.layout === 'admin' && authStore.isAuthenticated">
    <router-view />
  </AdminLayout>
  <!-- 无布局（登录页等） -->
  <router-view v-else />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'

const route = useRoute()
const authStore = useAuthStore()
</script>
