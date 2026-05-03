<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'

const route = useRoute()
const settingsStore = useSettingsStore()

const nav = [
  { name: 'Dashboard', to: '/', icon: 'M3 11.5L12 4l9 7.5M5.5 10.5v8a1 1 0 001 1h3.25v-5.25h4.5V19.5h3.25a1 1 0 001-1v-8' },
  { name: 'Trades', to: '/trades', icon: 'M6 20V10m6 10V4m6 16v-7M4.5 20h15' },
  { name: 'AI Decisions', to: '/ai', icon: 'M12 3v2m0 14v2m9-9h-2M5 12H3m15.364-6.364l-1.414 1.414M7.05 16.95l-1.414 1.414m0-12.728L7.05 7.05m9.9 9.9l1.414 1.414M9.5 14.5h5M10 17h4m-4.5-5a2.5 2.5 0 115 0c0 .9-.46 1.52-1.05 2.12-.44.45-.7.82-.82 1.38h-1.26c-.12-.56-.38-.93-.82-1.38-.59-.6-1.05-1.22-1.05-2.12z' },
  { name: 'AI Monitor', to: '/monitor', icon: 'M5 4h9l5 5v11H5V4zm9 0v5h5M8 15h8M8 18h5' },
  { name: 'Backtesting', to: '/backtest', icon: 'M12 8v5l3 2m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  { name: 'Admin', to: '/admin', icon: 'M12 15.5a3.5 3.5 0 100-7 3.5 3.5 0 000 7zm7.43-2.53a7.8 7.8 0 000-1.94l2.04-1.58-2-3.46-2.4.96a7.02 7.02 0 00-1.68-.98L15 3.4h-4l-.39 2.57c-.6.24-1.16.57-1.68.98l-2.4-.96-2 3.46 2.04 1.58a7.8 7.8 0 000 1.94L4.53 14.55l2 3.46 2.4-.96c.52.41 1.08.74 1.68.98L11 20.6h4l.39-2.57c.6-.24 1.16-.57 1.68-.98l2.4.96 2-3.46-2.04-1.58z' },
]

const isLiveMode = computed(() => settingsStore.settings['trading_mode'] === 'live')
const currentModel = computed(() => {
  const model = settingsStore.settings['ai_model']
  return model ? String(model) : 'Not loaded'
})

function isActive(path: string) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}
</script>

<template>
  <aside class="relative z-20 w-[264px] flex-shrink-0 flex-col border-r border-slate-800/75 bg-[#01040a]/92 px-4 py-6 shadow-2xl shadow-black/40 backdrop-blur-xl">
    <div class="flex items-center gap-3 px-1">
      <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-amber-300 to-amber-500 text-[11px] font-black text-slate-950 shadow-lg shadow-amber-500/15">
        XRP
      </div>
      <div class="min-w-0">
        <div class="truncate text-lg font-bold tracking-[-0.04em] text-slate-50">AI Trader</div>
        <div class="truncate text-sm text-slate-400">Paper Trading Lab</div>
      </div>
    </div>

    <nav class="mt-8 flex-1 space-y-2 overflow-y-auto pr-1">
      <RouterLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="liquid-nav-item group flex items-center gap-3 rounded-xl border px-4 py-3 text-base"
        :class="isActive(item.to)
          ? 'border-slate-500/45 bg-gradient-to-r from-slate-700/45 to-slate-800/20 text-slate-50 shadow-lg shadow-black/20'
          : 'border-transparent text-slate-400 hover:border-slate-700/55 hover:bg-slate-900/45 hover:text-slate-100'"
      >
        <svg
          class="h-5 w-5 flex-shrink-0"
          :class="isActive(item.to) ? 'text-amber-400' : 'text-slate-500 group-hover:text-slate-300'"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
        </svg>
        <span class="truncate">{{ item.name }}</span>
      </RouterLink>
    </nav>

    <div class="space-y-3 pt-5">
      <div class="inline-flex min-w-[116px] items-center justify-center gap-2 rounded-lg border border-slate-600/45 bg-slate-900/40 px-4 py-2 text-sm font-bold text-amber-300">
        <span class="h-2 w-2 rounded-full bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.65)]" />
        {{ isLiveMode ? 'LIVE' : 'PAPER' }}
      </div>

      <div class="rounded-xl border border-slate-600/45 bg-slate-900/45 p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-500/35 bg-slate-950/40 text-slate-300">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3l7 3v5c0 4.2-2.9 8.1-7 9-4.1-.9-7-4.8-7-9V6l7-3zm-3 9l2 2 4-5" />
            </svg>
          </div>
          <div class="min-w-0">
            <div class="truncate text-sm font-semibold text-slate-100">{{ isLiveMode ? 'Live Trading' : 'Paper Trading' }}</div>
            <div class="truncate text-xs text-slate-500">{{ isLiveMode ? 'Kraken execution enabled' : 'Simulated environment' }}</div>
          </div>
        </div>
        <div class="mt-3 truncate text-[11px] text-slate-600">Model: {{ currentModel }}</div>
      </div>
    </div>
  </aside>
</template>
