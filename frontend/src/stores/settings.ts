import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'
import type { SettingsResponse } from '@/api/types'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Record<string, unknown>>({})
  const meta = ref<SettingsResponse['meta']>({})
  const loading = ref(false)
  const saving = ref(false)
  const adminKey = ref(sessionStorage.getItem('adminSession') || '')
  sessionStorage.removeItem('adminKey')

  const isAdmin = computed(() => adminKey.value.length > 0)

  function setAdminKey(key: string) {
    adminKey.value = key
    sessionStorage.removeItem('adminKey')
    sessionStorage.setItem('adminSession', key)
  }

  function clearAdminKey() {
    adminKey.value = ''
    sessionStorage.removeItem('adminKey')
    sessionStorage.removeItem('adminSession')
  }

  async function fetchSettings() {
    loading.value = true
    try {
      const res = await api.get<SettingsResponse>('/admin/settings')
      settings.value = res.data.settings
      meta.value = res.data.meta
    } finally {
      loading.value = false
    }
  }

  async function verifySession() {
    try {
      await fetchSettings()
      return true
    } catch {
      clearAdminKey()
      return false
    }
  }

  async function saveSettings(updates: Record<string, unknown>) {
    saving.value = true
    try {
      await api.put('/admin/settings', { updates })
      await fetchSettings()
    } finally {
      saving.value = false
    }
  }

  async function saveSetting(key: string, value: unknown) {
    return saveSettings({ [key]: value })
  }

  return {
    settings,
    meta,
    loading,
    saving,
    adminKey,
    isAdmin,
    setAdminKey,
    clearAdminKey,
    fetchSettings,
    verifySession,
    saveSettings,
    saveSetting,
  }
})
