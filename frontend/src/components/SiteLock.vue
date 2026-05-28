<script setup lang="ts">
import { onUnmounted, ref } from 'vue'
import axios from 'axios'
import { usePinPad, NUMPAD_KEYS } from '@/composables/usePinPad'

const SESSION_KEY = 'site_unlocked'
const emit = defineEmits<{ unlocked: [] }>()

const error = ref('')
const loading = ref(false)
const locked = ref(false)
let lockTimer: ReturnType<typeof setTimeout> | null = null
let retryTickTimer: ReturnType<typeof setInterval> | null = null
const retrySeconds = ref(0)

const PIN_LENGTH = 6

const { pin, shaking, pressKey: basePressKey, reset, triggerShake } = usePinPad(PIN_LENGTH, submit)

function pressKey(key: string | number) {
  if (locked.value || loading.value) return
  error.value = ''
  basePressKey(key)
}

async function submit(pinValue: string) {
  if (locked.value || loading.value) return
  loading.value = true
  error.value = ''

  try {
    await axios.post('/api/v1/auth/login', { pin: pinValue }, { withCredentials: true })
    sessionStorage.removeItem('adminKey')
    sessionStorage.setItem('adminSession', '1')
    sessionStorage.setItem(SESSION_KEY, '1')
    emit('unlocked')
  } catch (e: unknown) {
    reset()
    triggerShake()
    if (axios.isAxiosError(e) && e.response?.status === 429) {
      locked.value = true
      error.value = e.response.data?.detail ?? 'Too many attempts. Please wait and try again.'
      retrySeconds.value = Number(e.response.headers['retry-after'] || 60)
      if (retryTickTimer) clearInterval(retryTickTimer)
      retryTickTimer = setInterval(() => {
        retrySeconds.value = Math.max(0, retrySeconds.value - 1)
      }, 1000)
      lockTimer = setTimeout(() => {
        locked.value = false
        error.value = ''
        retrySeconds.value = 0
        if (retryTickTimer) {
          clearInterval(retryTickTimer)
          retryTickTimer = null
        }
        lockTimer = null
      }, retrySeconds.value * 1000)
    } else {
      error.value = 'Incorrect PIN.'
    }
  } finally {
    loading.value = false
  }
}

onUnmounted(() => {
  if (lockTimer) clearTimeout(lockTimer)
  if (retryTickTimer) clearInterval(retryTickTimer)
})
</script>

<template>
  <div class="fixed inset-0 z-[9999] flex items-center justify-center overflow-hidden bg-[#070b10]">
    <div class="relative z-10 w-full max-w-xs mx-4 animate-scale-in">
      <div class="glass-pin-card glass-shimmer p-8 space-y-7">
        <div class="flex flex-col items-center gap-2">
          <div class="relative mb-1">
            <div class="relative w-14 h-14 rounded-lg flex items-center justify-center" style="background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.35);">
              <svg class="w-7 h-7 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.75">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
          </div>
          <h1 class="text-base font-bold text-gray-100 tracking-tight">XRP AI Trader</h1>
          <p class="text-xs text-gray-500">Enter your PIN to continue</p>
        </div>

        <div :class="['flex justify-center gap-3 py-1', shaking ? 'animate-shake' : '']">
          <div
            v-for="i in PIN_LENGTH"
            :key="i"
            class="w-3.5 h-3.5 rounded-full transition-all duration-200"
            :style="i <= pin.length
              ? 'background: #f59e0b; box-shadow: 0 0 10px rgba(245,158,11,0.7), 0 0 20px rgba(245,158,11,0.3); transform: scale(1.15);'
              : 'background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);'"
          />
        </div>

        <div class="h-4 -mt-3 text-center">
          <p v-if="error" class="text-xs text-rose-400">{{ error }}</p>
          <p v-else-if="locked" class="text-xs text-amber-500">Locked. Please wait {{ retrySeconds }}s...</p>
          <div v-else-if="loading" class="flex justify-center">
            <div class="w-4 h-4 border border-amber-400 border-t-transparent rounded-full animate-spin" />
          </div>
        </div>

        <div class="grid grid-cols-3 gap-2.5">
          <button
            v-for="key in NUMPAD_KEYS"
            :key="String(key)"
            @click="key !== '' ? pressKey(key) : undefined"
            :disabled="locked || loading || key === ''"
            :class="[
              'h-14 rounded-lg text-sm font-semibold transition-all duration-150 select-none',
              key === ''
                ? 'invisible'
                : key === 'Del'
                  ? 'text-gray-400 hover:text-gray-200 active:scale-95'
                  : 'text-gray-100 active:scale-95',
              (locked || loading) ? 'opacity-40 cursor-not-allowed' : ''
            ]"
            :style="key === '' ? '' : key === 'Del'
              ? 'background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);'
              : 'background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.09); box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset;'"
          >
            {{ key }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
