import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/client'
import type { Portfolio, Metrics } from '@/api/types'

export const usePortfolioStore = defineStore('portfolio', () => {
  const portfolio = ref<Portfolio | null>(null)
  const metrics = ref<Metrics | null>(null)
  const loading = ref(false)

  async function fetchPortfolio() {
    const res = await api.get<Portfolio>('/portfolio')
    portfolio.value = res.data
  }

  async function fetchMetrics() {
    loading.value = true
    try {
      const res = await api.get<Metrics>('/metrics')
      metrics.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function resetPortfolio() {
    const res = await api.post<Portfolio>('/admin/portfolio/reset')
    portfolio.value = res.data
  }

  return { portfolio, metrics, loading, fetchPortfolio, fetchMetrics, resetPortfolio }
})
