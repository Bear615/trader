import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'
import { useSettingsStore } from '@/stores/settings'
import type { PricePoint } from '@/api/types'

export const usePriceStore = defineStore('price', () => {
  const current = ref<PricePoint | null>(null)
  const history = ref<PricePoint[]>([])
  const loading = ref(false)
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)

  const change24h = computed(() => {
    if (!current.value?.price || !current.value?.price_yesterday) return null
    return ((current.value.price - current.value.price_yesterday) / current.value.price_yesterday) * 100
  })

  async function fetchCurrent() {
    const res = await api.get<PricePoint>('/prices/current')
    current.value = res.data
  }

  async function fetchHistory(timeframe = '24h', limit = 500) {
    loading.value = true
    try {
      const res = await api.get<PricePoint[]>('/prices/history', {
        params: { timeframe, limit },
      })
      history.value = res.data
    } finally {
      loading.value = false
    }
  }

  function connectWebSocket() {
    if (ws.value) return
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const key = encodeURIComponent(useSettingsStore().adminKey)
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/price?key=${key}`)

    socket.onopen = () => { connected.value = true }
    socket.onmessage = (event) => {
      const point: PricePoint = JSON.parse(event.data)
      current.value = point
      history.value.push(point)
      // Keep a rolling 5000-point window to avoid memory bloat
      if (history.value.length > 5000) history.value.shift()
    }
    socket.onclose = () => {
      connected.value = false
      ws.value = null
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }
    socket.onerror = () => { socket.close() }
    ws.value = socket
  }

  function disconnect() {
    ws.value?.close()
    ws.value = null
    connected.value = false
  }

  return { current, history, loading, connected, change24h, fetchCurrent, fetchHistory, connectWebSocket, disconnect }
})
