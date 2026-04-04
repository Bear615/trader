<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { usePortfolioStore } from '@/stores/portfolio'
import { usePriceStore } from '@/stores/price'
import SettingsField from '@/components/SettingsField.vue'
import { usePinPad, NUMPAD_KEYS } from '@/composables/usePinPad'
import api from '@/api/client'
import axios from 'axios'

const settingsStore = useSettingsStore()
const route = useRoute()
const router = useRouter()

const routeLabels: Record<string, string> = {
  backtest: 'Backtesting',
}
const redirectedFrom = computed(() => {
  const name = route.query.redirect as string | undefined
  return name ? (routeLabels[name] ?? name) : null
})
const portfolioStore = usePortfolioStore()
const priceStore = usePriceStore()

const loginError = ref('')
const loginLocked = ref(false)
const PIN_LENGTH = 6

const {
  pin: keyInput,
  shaking: loginShaking,
  pressKey: basePressKey,
  reset: resetPin,
  triggerShake,
} = usePinPad(PIN_LENGTH, loginWithPin)

function loginPressKey(key: string | number) {
  if (loginLocked.value) return
  loginError.value = ''
  basePressKey(key)
}

const saveStatus = ref<Record<string, 'idle' | 'saving' | 'saved' | 'error'>>({})
const dangerLoading = ref<Record<string, boolean>>({})
const successMsg = ref('')
const errorMsg = ref('')

// Live mode toggle state
const showLiveConfirmModal = ref(false)
const krakenTestResult = ref<{ ok: boolean; usd?: number; xrp?: number; error?: string } | null>(null)
const krakenTestLoading = ref(false)
const krakenSyncLoading = ref(false)

const isLiveMode = computed(() => settingsStore.settings['trading_mode'] === 'live')

onMounted(async () => {
  if (settingsStore.isAdmin) {
    await settingsStore.fetchSettings()
  }
})

async function loginWithPin(pinValue: string) {
  loginError.value = ''
  loginLocked.value = false
  try {
    const res = await api.post<{ token: string }>('/auth/login', { pin: pinValue })
    settingsStore.setAdminKey(res.data.token)
    await settingsStore.fetchSettings()
    const redirect = route.query.redirect as string | undefined
    if (redirect) {
      router.push({ name: redirect })
    } else {
      router.push({ name: 'dashboard' })
    }
  } catch (e: unknown) {
    resetPin()
    triggerShake()
    settingsStore.clearAdminKey()
    if (axios.isAxiosError(e) && e.response?.status === 429) {
      loginLocked.value = true
      loginError.value = e.response.data?.detail ?? 'Too many attempts. Please wait and try again.'
    } else {
      loginError.value = 'Incorrect PIN.'
    }
  }
}

// Keep backward compat alias used by template
function login() { loginWithPin(keyInput.value) }

function logout() {
  settingsStore.clearAdminKey()
}

async function saveSetting(key: string, value: unknown) {
  saveStatus.value[key] = 'saving'
  try {
    await settingsStore.saveSetting(key, value)
    saveStatus.value[key] = 'saved'
    setTimeout(() => { saveStatus.value[key] = 'idle' }, 2000)
  } catch {
    saveStatus.value[key] = 'error'
    setTimeout(() => { saveStatus.value[key] = 'idle' }, 3000)
  }
}

// Trading mode toggle
function requestModeToggle() {
  if (!isLiveMode.value) {
    // Switching to live — require confirmation
    showLiveConfirmModal.value = true
  } else {
    // Switching back to paper — no confirmation needed
    saveSetting('trading_mode', 'paper')
  }
}

async function confirmGoLive() {
  showLiveConfirmModal.value = false
  await saveSetting('trading_mode', 'live')
}

// Kraken utilities
async function testKrakenConnection() {
  krakenTestResult.value = null
  krakenTestLoading.value = true
  try {
    const res = await api.post('/admin/kraken/test-connection')
    krakenTestResult.value = { ok: true, usd: res.data.usd, xrp: res.data.xrp }
  } catch (e: unknown) {
    const msg = axios.isAxiosError(e) ? (e.response?.data?.detail ?? e.message) : String(e)
    krakenTestResult.value = { ok: false, error: msg }
  } finally {
    krakenTestLoading.value = false
  }
}

async function syncKrakenBalance() {
  krakenSyncLoading.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await api.post('/admin/kraken/sync-balance')
    successMsg.value = `Balances synced — USD: $${res.data.usd.toFixed(2)}, XRP: ${res.data.xrp.toFixed(6)}`
    setTimeout(() => { successMsg.value = '' }, 5000)
  } catch (e: unknown) {
    errorMsg.value = axios.isAxiosError(e) ? (e.response?.data?.detail ?? e.message) : String(e)
  } finally {
    krakenSyncLoading.value = false
  }
}

const groups = computed(() => [
  {
    id: 'data',
    label: 'Exchange & Data',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    keys: ['poll_interval_seconds', 'price_history_retention_days'],
  },
  {
    id: 'portfolio',
    label: 'Portfolio & Fees',
    icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    keys: ['starting_budget_usd', 'maker_fee_pct', 'taker_fee_pct'],
  },
  {
    id: 'ai',
    label: 'AI Configuration',
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    keys: ['ai_enabled', 'ai_model', 'ai_temperature', 'ai_decision_interval_seconds', 'ai_price_window', 'ai_max_prompt_tokens', 'ai_price_change_threshold_pct', 'ai_max_trade_pct', 'ai_system_prompt'],
  },
  {
    id: 'ai_provider',
    label: 'AI Provider',
    icon: 'M5 12h14M12 5l7 7-7 7',
    keys: ['ai_provider_preset', 'ai_base_url', 'ai_api_key', 'ai_use_tools', 'ai_ollama_timeout_seconds'],
  },
  {
    id: 'risk',
    label: 'Risk Management',
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    keys: ['risk_stop_loss_pct', 'risk_take_profit_pct', 'risk_max_daily_trades', 'risk_max_drawdown_pct', 'risk_min_trade_usd', 'risk_max_position_pct'],
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9',
    keys: ['telegram_enabled', 'telegram_bot_token', 'telegram_chat_id', 'telegram_notify_trades', 'telegram_notify_decisions', 'telegram_notify_errors'],
  },
  {
    id: 'display',
    label: 'Display',
    icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2',
    keys: ['ui_chart_default_timeframe', 'ui_trades_per_page', 'ui_price_decimals', 'ui_refresh_interval_seconds'],
  },
])

const openGroup = ref<string | null>('portfolio')

// Danger zone actions
async function doAction(key: string, fn: () => Promise<void>) {
  dangerLoading.value[key] = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    await fn()
    successMsg.value = 'Done.'
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (e: unknown) {
    if (axios.isAxiosError(e)) {
      errorMsg.value = e.response?.data?.detail || e.message
    } else {
      errorMsg.value = String(e)
    }
  } finally {
    dangerLoading.value[key] = false
  }
}

async function resetPortfolio() {
  await doAction('reset', () => portfolioStore.resetPortfolio())
}

async function seedHistory() {
  await doAction('seed', () => api.post('/admin/seed-history?days=30').then(() => {}))
}

async function clearPrices() {
  await doAction('clearPrices', () => api.delete('/admin/history/prices').then(() => {}))
}

async function clearTrades() {
  await doAction('clearTrades', () => api.delete('/admin/history/trades').then(() => {}))
}
</script>

<template>
  <div class="space-y-6 max-w-[900px]">
    <!-- Login gate -->
    <div v-if="!settingsStore.isAdmin" class="flex justify-center mt-12 animate-scale-in">
      <div class="w-full max-w-xs">
        <div class="glass-pin-card glass-shimmer p-8 space-y-7">
          <!-- Header -->
          <div class="flex flex-col items-center gap-2">
            <div class="relative mb-1">
              <div class="absolute inset-0 rounded-2xl blur-md" style="background: rgba(245,158,11,0.20);" />
              <div class="relative w-14 h-14 rounded-2xl flex items-center justify-center" style="background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.30);">
                <svg class="w-7 h-7 text-amber-400" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </div>
            <h2 class="text-base font-semibold text-gray-100 tracking-tight">Access Required</h2>
            <p class="text-xs text-gray-500">Enter your PIN to access admin</p>
          </div>

          <!-- Redirect notice -->
          <div v-if="redirectedFrom" class="flex items-start gap-2 rounded-xl px-3 py-2.5 text-xs text-amber-300" style="background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.20);">
            <svg class="w-3.5 h-3.5 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Admin access required for <strong class="text-amber-200">{{ redirectedFrom }}</strong>.</span>
          </div>

          <!-- PIN dots -->
          <div :class="['flex justify-center gap-3 py-1', loginShaking ? 'animate-shake' : '']">
            <div
              v-for="i in PIN_LENGTH"
              :key="i"
              class="w-3.5 h-3.5 rounded-full transition-all duration-200"
              :style="i <= keyInput.length
                ? 'background: #f59e0b; box-shadow: 0 0 10px rgba(245,158,11,0.7), 0 0 20px rgba(245,158,11,0.3); transform: scale(1.15);'
                : 'background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);'"
            />
          </div>

          <!-- Status messages -->
          <div class="h-4 -mt-3 text-center">
            <p v-if="loginError" :class="loginLocked ? 'text-xs text-amber-400' : 'text-xs text-rose-400'">{{ loginError }}</p>
            <p v-else-if="loginLocked" class="text-xs text-amber-500">Locked. Please wait…</p>
          </div>

          <!-- Numpad -->
          <div class="grid grid-cols-3 gap-2.5">
            <button
              v-for="key in NUMPAD_KEYS"
              :key="String(key)"
              @click="key !== '' ? loginPressKey(key) : undefined"
              :disabled="loginLocked || key === ''"
              :class="[
                'h-14 rounded-2xl text-sm font-semibold transition-all duration-150 select-none',
                key === ''
                  ? 'invisible'
                  : key === '⌫'
                    ? 'text-gray-400 hover:text-gray-200 active:scale-95'
                    : 'text-gray-100 active:scale-95',
                loginLocked ? 'opacity-40 cursor-not-allowed' : key !== '' ? 'cursor-pointer' : ''
              ]"
              :style="key === '' ? '' : key === '⌫'
                ? 'background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);'
                : 'background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.09); box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset;'"
            >
              {{ key }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Admin panel content -->
    <template v-else>
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-gray-100">Admin Panel</h1>
          <p class="text-sm text-gray-500 mt-0.5">All settings, controls, and danger zone</p>
        </div>
        <button @click="logout" class="btn btn-ghost btn-sm text-gray-500">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Logout
        </button>
      </div>

      <!-- Settings groups accordion -->
      <div class="space-y-3">
        <div
          v-for="group in groups"
          :key="group.id"
          class="rounded-xl overflow-hidden" style="background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%); border: 1px solid rgba(255,255,255,0.09); backdrop-filter: blur(16px);"
        >
          <!-- Accordion header -->
          <button
            @click="openGroup = openGroup === group.id ? null : group.id"
            class="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/[0.04] transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center">
                <svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" :d="group.icon" />
                </svg>
              </div>
              <span class="text-sm font-semibold text-gray-200">{{ group.label }}</span>
            </div>
            <svg
              class="w-4 h-4 text-gray-500 transition-transform duration-200"
              :class="{ 'rotate-180': openGroup === group.id }"
              fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Settings fields -->
          <div v-show="openGroup === group.id" class="px-5 pb-5 space-y-4" style="border-top: 1px solid rgba(255,255,255,0.07);">
            <SettingsField
              v-for="key in group.keys"
              :key="key"
              :setting-key="key"
              :value="settingsStore.settings[key]"
              :meta="settingsStore.meta[key]"
              :status="saveStatus[key] ?? 'idle'"
              @save="(v) => saveSetting(key, v)"
            />
          </div>
        </div>

        <!-- Live Trading Mode accordion (amber, always last) -->
        <div class="rounded-xl border overflow-hidden"
          :style="isLiveMode ? 'background: rgba(120,53,15,0.18); border-color: rgba(245,158,11,0.45);' : 'background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%); border-color: rgba(255,255,255,0.09); backdrop-filter: blur(16px);'">
          <button
            @click="openGroup = openGroup === 'live' ? null : 'live'"
            class="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-amber-500/5 transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                :class="isLiveMode ? 'bg-amber-500/20 border border-amber-500/40' : 'bg-amber-500/10 border border-amber-500/20'">
                <svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-sm font-semibold text-gray-200">Live Trading Mode</span>
                <span v-if="isLiveMode" class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/20 border border-red-500/40 text-xs font-bold text-red-400">
                  <span class="relative flex h-1.5 w-1.5">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                    <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-red-400" />
                  </span>
                  LIVE
                </span>
                <span v-else class="px-2 py-0.5 rounded-full bg-slate-500/20 border border-slate-500/30 text-xs font-semibold text-slate-400">PAPER</span>
              </div>
            </div>
            <svg
              class="w-4 h-4 text-gray-500 transition-transform duration-200"
              :class="{ 'rotate-180': openGroup === 'live' }"
              fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-show="openGroup === 'live'" class="px-5 pb-5 space-y-5 border-t"
            :style="isLiveMode ? 'border-color: rgba(245,158,11,0.28);' : 'border-color: rgba(255,255,255,0.07);'">

            <!-- Warning banner -->
            <div class="flex items-start gap-3 rounded-lg bg-amber-500/10 border border-amber-500/25 px-4 py-3 mt-4">
              <svg class="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.07 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <p class="text-xs text-amber-300 leading-relaxed">
                <strong class="text-amber-200">Live mode uses real money.</strong>
                Orders are placed directly on Kraken with your account funds. All risk settings still apply, but losses are real.
                API keys are stored as plaintext in the local database.
              </p>
            </div>

            <!-- Mode toggle -->
            <div class="flex items-center justify-between">
              <div>
                <div class="text-sm font-medium text-gray-200">Trading Mode</div>
                <div class="text-xs text-gray-500 mt-0.5">{{ isLiveMode ? 'Sending real orders to Kraken' : 'Simulated paper trading (no real money)' }}</div>
              </div>
              <button
                @click="requestModeToggle"
                :disabled="saveStatus['trading_mode'] === 'saving'"
                class="relative inline-flex h-7 w-14 flex-shrink-0 cursor-pointer rounded-full border-2 transition-colors duration-200 ease-in-out focus:outline-none"
                :class="isLiveMode ? 'bg-red-500 border-red-500' : 'border-white/20'" :style="isLiveMode ? '' : 'background: rgba(255,255,255,0.1);'"
              >
                <span
                  class="pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform transition duration-200 ease-in-out mt-px"
                  :class="isLiveMode ? 'translate-x-7' : 'translate-x-0.5'"
                />
              </button>
            </div>

            <!-- Kraken credentials (always visible in this section) -->
            <div class="space-y-4">
              <SettingsField
                setting-key="kraken_api_key"
                :value="settingsStore.settings['kraken_api_key']"
                :meta="settingsStore.meta['kraken_api_key']"
                :status="saveStatus['kraken_api_key'] ?? 'idle'"
                @save="(v) => saveSetting('kraken_api_key', v)"
              />
              <SettingsField
                setting-key="kraken_api_secret"
                :value="settingsStore.settings['kraken_api_secret']"
                :meta="settingsStore.meta['kraken_api_secret']"
                :status="saveStatus['kraken_api_secret'] ?? 'idle'"
                @save="(v) => saveSetting('kraken_api_secret', v)"
              />
              <SettingsField
                setting-key="kraken_pair"
                :value="settingsStore.settings['kraken_pair']"
                :meta="settingsStore.meta['kraken_pair']"
                :status="saveStatus['kraken_pair'] ?? 'idle'"
                @save="(v) => saveSetting('kraken_pair', v)"
              />
              <SettingsField
                setting-key="kraken_order_type"
                :value="settingsStore.settings['kraken_order_type']"
                :meta="settingsStore.meta['kraken_order_type']"
                :status="saveStatus['kraken_order_type'] ?? 'idle'"
                @save="(v) => saveSetting('kraken_order_type', v)"
              />
              <SettingsField
                setting-key="kraken_balance_sync_interval_minutes"
                :value="settingsStore.settings['kraken_balance_sync_interval_minutes']"
                :meta="settingsStore.meta['kraken_balance_sync_interval_minutes']"
                :status="saveStatus['kraken_balance_sync_interval_minutes'] ?? 'idle'"
                @save="(v) => saveSetting('kraken_balance_sync_interval_minutes', v)"
              />
            </div>

            <!-- Test connection button + result -->
            <div class="flex items-center gap-3 pt-1">
              <button
                @click="testKrakenConnection"
                :disabled="krakenTestLoading"
                class="btn btn-ghost btn-sm"
              >
                <div v-if="krakenTestLoading" class="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin" />
                Test Connection
              </button>
              <button
                v-if="isLiveMode"
                @click="syncKrakenBalance"
                :disabled="krakenSyncLoading"
                class="btn btn-ghost btn-sm"
              >
                <div v-if="krakenSyncLoading" class="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin" />
                Sync Balance Now
              </button>
            </div>
            <div v-if="krakenTestResult !== null" class="rounded-lg px-3 py-2 text-xs font-mono"
              :class="krakenTestResult.ok ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300' : 'bg-rose-500/10 border border-rose-500/20 text-rose-300'">
              <template v-if="krakenTestResult.ok">
                Connected — USD: ${{ krakenTestResult.usd?.toFixed(2) }}, XRP: {{ krakenTestResult.xrp?.toFixed(6) }}
              </template>
              <template v-else>
                {{ krakenTestResult.error }}
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Danger Zone -->
      <div class="rounded-2xl border border-rose-900/50 p-5 space-y-4" style="background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,0,0,0.02) 100%); backdrop-filter: blur(16px);">
        <div class="flex items-center gap-2 pb-3" style="border-bottom: 1px solid rgba(255,255,255,0.07);">
          <svg class="w-4 h-4 text-rose-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.07 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <h2 class="text-sm font-semibold text-rose-400">Danger Zone</h2>
        </div>

        <div v-if="successMsg" class="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded px-3 py-2">
          {{ successMsg }}
        </div>
        <div v-if="errorMsg" class="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded px-3 py-2">
          {{ errorMsg }}
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="card-sm space-y-2">
            <div class="text-sm font-medium text-gray-300">Seed Price History</div>
            <p class="text-xs text-gray-500">Fetch 30 days of XRP price data from CoinGecko for backtesting.</p>
            <button @click="seedHistory" :disabled="dangerLoading['seed']" class="btn btn-ghost btn-sm">
              <div v-if="dangerLoading['seed']" class="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin" />
              Seed from CoinGecko
            </button>
          </div>

          <div class="card-sm space-y-2">
            <div class="text-sm font-medium text-gray-300">Reset Portfolio</div>
            <p class="text-xs text-gray-500">Reset USD balance to starting budget; wipe XRP balance. Trades are kept.</p>
            <button @click="resetPortfolio" :disabled="dangerLoading['reset']" class="btn btn-danger btn-sm">
              <div v-if="dangerLoading['reset']" class="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
              Reset Portfolio
            </button>
          </div>

          <div class="card-sm space-y-2">
            <div class="text-sm font-medium text-gray-300">Clear Price History</div>
            <p class="text-xs text-gray-500">Delete all stored price points from the database. Irreversible.</p>
            <button @click="clearPrices" :disabled="dangerLoading['clearPrices']" class="btn btn-danger btn-sm">
              <div v-if="dangerLoading['clearPrices']" class="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
              Clear Prices
            </button>
          </div>

          <div class="card-sm space-y-2">
            <div class="text-sm font-medium text-gray-300">Clear Trade History</div>
            <p class="text-xs text-gray-500">Delete all paper trades and AI decisions. Irreversible.</p>
            <button @click="clearTrades" :disabled="dangerLoading['clearTrades']" class="btn btn-danger btn-sm">
              <div v-if="dangerLoading['clearTrades']" class="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
              Clear Trades
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>

  <!-- Live mode confirmation modal -->
  <Teleport to="body">
    <div v-if="showLiveConfirmModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div class="w-full max-w-md mx-4 rounded-2xl border border-amber-500/40 bg-[#0f0f12] shadow-2xl p-6 space-y-5">
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-xl bg-red-500/15 border border-red-500/30 flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.07 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div>
            <h3 class="text-base font-semibold text-gray-100">Enable Live Trading?</h3>
            <p class="text-xs text-gray-400 mt-1">You are about to switch to live mode.</p>
          </div>
        </div>
        <ul class="space-y-2 text-xs text-amber-200/90">
          <li class="flex items-start gap-2">
            <span class="text-amber-400 flex-shrink-0 mt-0.5">▸</span>
            All trades will execute as <strong>real orders on Kraken</strong> using your API credentials.
          </li>
          <li class="flex items-start gap-2">
            <span class="text-amber-400 flex-shrink-0 mt-0.5">▸</span>
            Losses incurred are <strong>real monetary losses</strong>. There is no undo.
          </li>
          <li class="flex items-start gap-2">
            <span class="text-amber-400 flex-shrink-0 mt-0.5">▸</span>
            Risk settings (stop-loss, max position, etc.) are enforced but cannot guarantee safety.
          </li>
          <li class="flex items-start gap-2">
            <span class="text-amber-400 flex-shrink-0 mt-0.5">▸</span>
            The price feed will switch to Kraken's ticker API immediately.
          </li>
        </ul>
        <div class="flex gap-3 pt-1">
          <button @click="showLiveConfirmModal = false" class="btn btn-ghost flex-1">Cancel</button>
          <button @click="confirmGoLive" class="flex-1 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-sm font-semibold transition-colors">
            I understand — Go Live
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
