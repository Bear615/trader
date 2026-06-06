import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/client'
import type { Portfolio, Metrics, ResetPnlResponse } from '@/api/types'

export const usePortfolioStore = defineStore('portfolio', () => {
  const portfolio = ref<Portfolio | null>(null)
  const metrics = ref<Metrics | null>(null)
  const loading = ref(false)
  const lastPnlResetAt = ref<string | null>(null)

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

  async function resetROI() {
    const res = await api.post<Portfolio>('/admin/portfolio/reset-roi')
    portfolio.value = res.data
  }

  async function resetPnl() {
    const res = await api.post<ResetPnlResponse>('/admin/portfolio/reset-pnl')
    lastPnlResetAt.value = res.data.reset_at
    metrics.value = {
      ...((metrics.value ?? {}) as Metrics),
      realized_pnl_usd: res.data.realized_pnl_usd,
      unrealized_pnl_usd: res.data.unrealized_pnl_usd,
      total_pnl_usd: res.data.total_pnl_usd,
      open_cost_basis_usd: res.data.open_cost_basis_usd ?? res.data.cost_basis,
      avg_buy_price: res.data.open_xrp > 0 && res.data.cost_basis > 0 ? res.data.cost_basis / res.data.open_xrp : null,
      pnl_reset_at: res.data.reset_at,
    }
    await fetchMetrics()
    return res.data
  }

  return { portfolio, metrics, loading, lastPnlResetAt, fetchPortfolio, fetchMetrics, resetPortfolio, resetROI, resetPnl }
})
