<script setup lang="ts">
import { ref } from 'vue'

const SITE_PIN = import.meta.env.VITE_SITE_PIN as string
const SESSION_KEY = 'site_unlocked'

const emit = defineEmits<{ unlocked: [] }>()

const pin = ref('')
const error = ref('')
const attempts = ref(0)
const locked = ref(false)
let lockTimer: ReturnType<typeof setTimeout> | null = null

function submit() {
  if (locked.value) return
  if (pin.value === SITE_PIN) {
    sessionStorage.setItem(SESSION_KEY, '1')
    emit('unlocked')
  } else {
    pin.value = ''
    attempts.value++
    if (attempts.value >= 5) {
      locked.value = true
      error.value = 'Too many attempts. Try again in 30 seconds.'
      lockTimer = setTimeout(() => {
        locked.value = false
        attempts.value = 0
        error.value = ''
        lockTimer = null
      }, 30_000)
    } else {
      error.value = 'Incorrect PIN.'
    }
  }
}
</script>

<template>
  <div class="fixed inset-0 z-[9999] flex items-center justify-center bg-surface-950">
    <!-- Ambient blobs -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
      <div class="absolute -top-40 left-1/3 w-[600px] h-[600px] rounded-full blur-[140px] bg-sky-600/[0.07]" />
      <div class="absolute -bottom-32 right-1/4 w-[500px] h-[500px] rounded-full blur-[120px] bg-violet-600/[0.05]" />
    </div>

    <div class="relative z-10 w-full max-w-sm mx-4">
      <div class="rounded-2xl border border-white/[0.06] bg-surface-900/80 backdrop-blur-sm p-8 shadow-2xl">
        <div class="flex flex-col items-center gap-2 mb-8">
          <div class="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center mb-1">
            <svg class="w-6 h-6 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </div>
          <h1 class="text-lg font-semibold text-white tracking-tight">Enter site PIN</h1>
          <p class="text-sm text-white/40">Access is restricted</p>
        </div>

        <form @submit.prevent="submit" class="flex flex-col gap-4">
          <input
            v-model="pin"
            type="password"
            inputmode="numeric"
            autocomplete="off"
            :disabled="locked"
            placeholder="PIN"
            autofocus
            class="w-full rounded-lg bg-surface-800 border border-white/[0.08] px-4 py-3 text-white text-center text-xl tracking-[0.4em] placeholder:text-white/20 placeholder:tracking-normal focus:outline-none focus:ring-2 focus:ring-sky-500/50 disabled:opacity-40 transition"
          />

          <p v-if="error" class="text-xs text-red-400 text-center -mt-1">{{ error }}</p>

          <button
            type="submit"
            :disabled="locked || pin.length === 0"
            class="w-full rounded-lg bg-sky-500 hover:bg-sky-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium py-3 transition"
          >
            Unlock
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
