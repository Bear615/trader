<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const SESSION_KEY = 'site_unlocked'
const emit = defineEmits<{ unlocked: [] }>()

const pin = ref('')
const error = ref('')
const loading = ref(false)
const locked = ref(false)
let lockTimer: ReturnType<typeof setTimeout> | null = null

async function submit() {
  if (locked.value || loading.value || !pin.value) return
  loading.value = true
  error.value = ''

  try {
    const res = await axios.post<{ token: string }>('/api/v1/auth/login', { pin: pin.value })
    // Store the admin key in sessionStorage so the settings store and WS clients can use it
    sessionStorage.setItem('adminKey', res.data.token)
    sessionStorage.setItem(SESSION_KEY, '1')
    emit('unlocked')
  } catch (e: unknown) {
    pin.value = ''
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
  <div class="fixed inset-0 z-[9999] flex items-center justify-center bg-surface-950">
    <!-- Dot-grid — matches app background -->
    <div
      class="absolute inset-0 pointer-events-none"
      aria-hidden="true"
      style="background-image: radial-gradient(circle, #27272a 1px, transparent 1px); background-size: 28px 28px; opacity: 0.5;"
    />

    <div class="relative z-10 w-full max-w-xs mx-4">
      <!-- Amber top-accent card -->
      <div class="bg-surface-900 border border-surface-800 border-t-2 border-t-amber-500 rounded-lg p-8 shadow-xl">
        <!-- logo -->
        <div class="flex flex-col items-center gap-1 mb-8">
          <div class="w-9 h-9 rounded bg-amber-500 flex items-center justify-center mb-2">
            <svg class="w-5 h-5 text-zinc-950" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </div>
          <h1 class="text-base font-bold text-zinc-100 tracking-tight">XRP AI Trader</h1>
          <p class="text-xs text-zinc-500">Enter your PIN to continue</p>
        </div>

        <form @submit.prevent="submit" class="flex flex-col gap-3">
          <input
            v-model="pin"
            type="password"
            inputmode="numeric"
            autocomplete="off"
            :disabled="locked || loading"
            placeholder="••••••"
            autofocus
            class="w-full bg-surface-950 border border-surface-700 rounded-md px-4 py-3
                   text-zinc-100 text-center text-xl tracking-[0.5em] font-mono
                   placeholder:tracking-normal placeholder:text-zinc-600
                   focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500
                   disabled:opacity-40 transition-colors"
          />

          <p v-if="error" class="text-xs text-rose-400 text-center -mt-0.5">{{ error }}</p>
          <p v-if="locked && !error" class="text-xs text-amber-500 text-center -mt-0.5">Locked. Please wait…</p>

          <button
            type="submit"
            :disabled="locked || loading || !pin.length"
            class="w-full rounded-md bg-amber-500 hover:bg-amber-400 disabled:opacity-40
                   disabled:cursor-not-allowed text-zinc-950 font-semibold py-2.5
                   transition-colors duration-150 flex items-center justify-center gap-2"
          >
            <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>{{ loading ? 'Verifying…' : 'Unlock' }}</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
