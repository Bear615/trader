import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/client'
import { useSettingsStore } from '@/stores/settings'
import type { Trade, PaginatedResponse } from '@/api/types'

export const useTradesStore = defineStore('trades', () => {
  const items = ref<Trade[]>([])
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(25)
  const loading = ref(false)
  const actionFilter = ref<'BUY' | 'SELL' | null>(null)
  const ws = ref<WebSocket | null>(null)

  async function fetchTrades(p = 1) {
    loading.value = true
    page.value = p
    try {
      const params: Record<string, unknown> = { page: p, per_page: perPage.value }
      if (actionFilter.value) params.action = actionFilter.value
      const res = await api.get<PaginatedResponse<Trade>>('/trades', { params })
      items.value = res.data.items
      total.value = res.data.total
    } finally {
      loading.value = false
    }
  }

  function connectWebSocket() {
    if (ws.value) return
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const key = encodeURIComponent(useSettingsStore().adminKey)
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/trades?key=${key}`)
    socket.onmessage = (e) => {
      const trade: Trade = JSON.parse(e.data)
      items.value.unshift(trade)
      total.value++
      if (items.value.length > perPage.value) items.value.pop()
    }
    socket.onclose = () => {
      ws.value = null
      setTimeout(connectWebSocket, 3000)
    }
    socket.onerror = () => socket.close()
    ws.value = socket
  }

  return { items, total, page, perPage, loading, actionFilter, fetchTrades, connectWebSocket }
})
