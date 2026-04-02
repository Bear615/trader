import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { BacktestRun } from '@/api/types'
import api from '@/api/client'

export const useBacktestStore = defineStore('backtest', () => {
  const runs = ref<BacktestRun[]>([])
  const activeRun = ref<BacktestRun | null>(null)
  const polling = ref<ReturnType<typeof setInterval> | null>(null)
  const loading = ref(false)

  async function fetchRuns() {
    const res = await api.get<BacktestRun[]>('/admin/backtest')
    runs.value = res.data
  }

  async function fetchRun(id: number) {
    const res = await api.get<BacktestRun>(`/admin/backtest/${id}`)
    activeRun.value = res.data
    return res.data
  }

  async function startBacktest(config: {
    start_date: string
    end_date: string
    initial_capital: number
    maker_fee_pct: number
    taker_fee_pct: number
    decisions_per_hour: number
    ai_price_window: number
    ai_model: string
  }) {
    const res = await api.post<{ run_id: number; status: string }>('/admin/backtest', config)
    const { run_id } = res.data
    await fetchRuns()
    // Poll until done
    return new Promise<BacktestRun>((resolve) => {
      const interval = setInterval(async () => {
        const run = await fetchRun(run_id)
        if (run.status === 'done' || run.status === 'error') {
          clearInterval(interval)
          await fetchRuns()
          resolve(run)
        }
      }, 2000)
      polling.value = interval
    })
  }

  return { runs, activeRun, loading, fetchRuns, fetchRun, startBacktest }
})
