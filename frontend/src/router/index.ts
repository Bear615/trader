import { createRouter, createWebHistory } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/Dashboard.vue'),
    },
    {
      path: '/trades',
      name: 'trades',
      component: () => import('@/views/Trades.vue'),
    },
    {
      path: '/ai',
      name: 'ai',
      component: () => import('@/views/AIDecisions.vue'),
    },
    {
      path: '/backtest',
      name: 'backtest',
      component: () => import('@/views/Backtesting.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/monitor',
      name: 'monitor',
      component: () => import('@/views/AIMonitor.vue'),
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/Admin.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const store = useSettingsStore()

  // Redirect unauthenticated users to the login page (Admin view)
  if (to.name !== 'admin' && !store.isAdmin) {
    return { name: 'admin', query: { redirect: to.name as string } }
  }

  // Guard admin-only routes even when a key is present but not verified
  if (to.meta.requiresAdmin && !store.isAdmin) {
    return { name: 'admin', query: { redirect: to.name as string } }
  }
})

export default router
