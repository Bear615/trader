<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'

const route = useRoute()
const settingsStore = useSettingsStore()

const nav = [
  { name: 'Dashboard',    to: '/',         icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { name: 'Trades',       to: '/trades',   icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { name: 'AI Decisions', to: '/ai',       icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
  { name: 'AI Monitor',   to: '/monitor',  icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { name: 'Backtesting',  to: '/backtest', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  { name: 'Admin',        to: '/admin',    icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
]

const currentModel = computed(() => {
  const m = settingsStore.settings['ai_model']
  return m ? String(m) : '—'
})
</script>

<template>
  <aside class="w-56 flex-shrink-0 bg-surface-950 border-r border-surface-800 hidden md:flex flex-col relative z-20">
    <!-- Logo / wordmark -->
    <div class="h-14 flex items-center px-5 border-b border-surface-800 flex-shrink-0">
      <div class="flex items-center gap-2.5">
        <!-- Amber accent square -->
        <div class="w-7 h-7 rounded bg-amber-500 flex items-center justify-center flex-shrink-0">
          <span class="text-zinc-950 text-[10px] font-black tracking-tight leading-none">XRP</span>
        </div>
        <div class="min-w-0">
          <div class="text-sm font-bold tracking-tight text-zinc-100 leading-tight">AI Trader</div>
          <div class="text-[10px] text-zinc-500 leading-tight mt-px">Paper Trading Lab</div>
        </div>
      </div>
    </div>

    <!-- Nav items -->
    <nav class="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
      <RouterLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="group flex items-center gap-2.5 px-3 py-2 rounded text-sm font-medium transition-colors duration-150 relative"
        :class="route.path === item.to
          ? 'bg-surface-800 text-amber-400 border-l-2 border-l-amber-500 pl-[10px]'
          : 'text-zinc-500 hover:text-zinc-100 hover:bg-surface-800 border-l-2 border-l-transparent pl-[10px]'"
      >
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
        </svg>
        <span class="truncate">{{ item.name }}</span>
        <span
          v-if="item.name === 'Admin' && settingsStore.isAdmin"
          class="ml-auto text-[9px] px-1.5 py-px rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 font-bold flex-shrink-0"
        >ADMIN</span>
      </RouterLink>
    </nav>

    <!-- Footer -->
    <div class="px-5 py-3 border-t border-surface-800 flex-shrink-0">
      <p class="text-[10px] text-zinc-600 leading-relaxed">
        Data: DIA Oracle · XRPL<br />Model: {{ currentModel }}
      </p>
    </div>
  </aside>
</template>
