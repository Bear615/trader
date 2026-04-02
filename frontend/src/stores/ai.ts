import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/client'
import { useSettingsStore } from '@/stores/settings'
import type { AIDecision, PaginatedResponse } from '@/api/types'

export const useAIStore = defineStore('ai', () => {
  const items = ref<AIDecision[]>([])
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(25)
  const loading = ref(false)
  const ws = ref<WebSocket | null>(null)

  async function fetchDecisions(p = 1) {
    loading.value = true
    page.value = p
    try {
      const res = await api.get<PaginatedResponse<AIDecision>>('/ai/decisions', {
        params: { page: p, per_page: perPage.value },
      })
      items.value = res.data.items
      total.value = res.data.total
    } finally {
      loading.value = false
    }
  }

  async function triggerDecision() {
    const res = await api.post<AIDecision>('/admin/ai/trigger')
    return res.data
  }

  function connectWebSocket() {
    if (ws.value) return
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const key = encodeURIComponent(useSettingsStore().adminKey)
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/decisions?key=${key}`)
    socket.onmessage = (e) => {
      const decision: AIDecision = JSON.parse(e.data)
      items.value.unshift(decision)
      total.value++
    }
    socket.onclose = () => {
      ws.value = null
      setTimeout(connectWebSocket, 3000)
    }
    socket.onerror = () => socket.close()
    ws.value = socket
  }

  return { items, total, page, perPage, loading, fetchDecisions, triggerDecision, connectWebSocket }
})
