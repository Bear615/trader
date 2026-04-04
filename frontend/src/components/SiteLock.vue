<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { usePinPad, NUMPAD_KEYS } from '@/composables/usePinPad'

const SESSION_KEY = 'site_unlocked'
const emit = defineEmits<{ unlocked: [] }>()

const error = ref('')
const loading = ref(false)
const locked = ref(false)
let lockTimer: ReturnType<typeof setTimeout> | null = null

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
    const res = await axios.post<{ token: string }>('/api/v1/auth/login', { pin: pinValue })
    sessionStorage.setItem('adminKey', res.data.token)
    sessionStorage.setItem(SESSION_KEY, '1')
    emit('unlocked')
  } catch (e: unknown) {
    reset()
    triggerShake()
    if (axios.isAxiosError(e) && e.response?.status === 429) {
      locked.value = true
      error.value = e.response.data?.detail ?? 'Too many attempts. Please wait and try again.'
      lockTimer = setTimeout(() => {
        locked.value = false
        error.value = ''
        lockTimer = null
      }, 60_000)
    } else {
      error.value = 'Incorrect PIN.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-[9999] flex items-center justify-center overflow-hidden" style="background: #09090b;">
    <!-- Background layers -->
    <div class="absolute inset-0 pointer-events-none" aria-hidden="true">
      <div class="absolute inset-0" style="background-image: radial-gradient(circle, #27272a 1px, transparent 1px); background-size: 28px 28px; opacity: 0.45;" />
      <div class="absolute" style="top: 30%; left: 50%; transform: translate(-50%, -50%); width: 480px; height: 480px; border-radius: 50%; background: radial-gradient(circle, rgba(245,158,11,0.10) 0%, transparent 70%); filter: blur(48px);" />
      <div class="absolute" style="bottom: 10%; right: 10%; width: 320px; height: 320px; border-radius: 50%; background: radial-gradient(circle, rgba(56,189,248,0.06) 0%, transparent 70%); filter: blur(64px);" />
    </div>

    <!-- Card -->
    <div class="relative z-10 w-full max-w-xs mx-4 animate-scale-in">
      <div class="glass-pin-card glass-shimmer p-8 space-y-7">
        <!-- Logo -->
        <div class="flex flex-col items-center gap-2">
          <div class="relative mb-1">
            <div class="absolute inset-0 rounded-2xl blur-md" style="background: rgba(245,158,11,0.25);" />
            <div class="relative w-14 h-14 rounded-2xl flex items-center justify-center" style="background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.35);">
              <svg class="w-7 h-7 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.75">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
          </div>
          <h1 class="text-base font-bold text-gray-100 tracking-tight">XRP AI Trader</h1>
          <p class="text-xs text-gray-500">Enter your PIN to continue</p>
        </div>

        <!-- PIN dots -->
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

        <!-- Status messages -->
        <div class="h-4 -mt-3 text-center">
          <p v-if="error" class="text-xs text-rose-400">{{ error }}</p>
          <p v-else-if="locked" class="text-xs text-amber-500">Locked. Please wait…</p>
          <div v-else-if="loading" class="flex justify-center">
            <div class="w-4 h-4 border border-amber-400 border-t-transparent rounded-full animate-spin" />
          </div>
        </div>

        <!-- Numpad -->
        <div class="grid grid-cols-3 gap-2.5">
          <button
            v-for="key in NUMPAD_KEYS"
            :key="String(key)"
            @click="key !== '' ? pressKey(key) : undefined"
            :disabled="locked || loading || key === ''"
            :class="[
              'h-14 rounded-2xl text-sm font-semibold transition-all duration-150 select-none',
              key === ''
                ? 'invisible'
                : key === '⌫'
                  ? 'text-gray-400 hover:text-gray-200 active:scale-95'
                  : 'text-gray-100 active:scale-95',
              (locked || loading) ? 'opacity-40 cursor-not-allowed' : ''
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
</template>
