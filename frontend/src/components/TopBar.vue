<script setup lang="ts">
import { usePriceStore } from '@/stores/price'
import { usePortfolioStore } from '@/stores/portfolio'
import { useSettingsStore } from '@/stores/settings'
import { computed, onMounted } from 'vue'
import NumberTicker from './NumberTicker.vue'

const priceStore = usePriceStore()
const portfolioStore = usePortfolioStore()
const settingsStore = useSettingsStore()

onMounted(() => portfolioStore.fetchPortfolio())

const isLiveMode = computed(() => settingsStore.settings['trading_mode'] === 'live')

const priceColor = computed(() =>
  (priceStore.change24h ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
)
const changeSign = computed(() => (priceStore.change24h ?? 0) >= 0 ? '+' : '')

const formattedPrice = computed(() =>
  priceStore.current ? '$' + priceStore.current.price.toFixed(6) : ''
)
const formattedChange = computed(() =>
  priceStore.change24h !== null
    ? changeSign.value + priceStore.change24h.toFixed(2) + '%'
    : ''
)
const formattedPortfolio = computed(() => {
  const p = portfolioStore.portfolio
  if (!p) return ''
  return '$' + (p.total_value_usd ?? p.usd_balance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
})
const formattedRoi = computed(() => {
  const p = portfolioStore.portfolio
  if (!p || p.roi_pct === null) return ''
  return ((p.roi_pct ?? 0) >= 0 ? '+' : '') + p.roi_pct?.toFixed(2) + '% ROI'
})
</script>

<template>
  <header class="h-14 flex items-center justify-between px-6 bg-surface-950 border-b border-surface-800 flex-shrink-0 sticky top-0 z-30">
    <!-- Left: connection status + mode badge + price -->
    <div class="flex items-center gap-4">
      <!-- WS status dot -->
      <div class="flex items-center gap-1.5">
        <span class="relative flex h-1.5 w-1.5">
          <span v-if="priceStore.connected" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
          <span class="relative inline-flex rounded-full h-1.5 w-1.5" :class="priceStore.connected ? 'bg-amber-400' : 'bg-zinc-600'" />
        </span>
        <span class="text-[11px] font-semibold" :class="priceStore.connected ? 'text-amber-400' : 'text-zinc-600'">
          {{ priceStore.connected ? 'LIVE' : 'OFFLINE' }}
        </span>
      </div>

      <!-- Trading mode badge -->
      <div v-if="isLiveMode" class="flex items-center gap-1.5 px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/25">
        <span class="relative flex h-1.5 w-1.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
          <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-rose-400" />
        </span>
        <span class="text-[11px] font-bold text-rose-400 tracking-wide">LIVE</span>
      </div>
      <div v-else class="px-2 py-0.5 rounded bg-surface-800 border border-surface-700">
        <span class="text-[11px] font-semibold text-zinc-500 tracking-wide">PAPER</span>
      </div>

      <div class="w-px h-4 bg-surface-700" />

      <!-- Price ticker -->
      <div class="flex items-center gap-3">
        <span class="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">XRP/USD</span>
        <div v-if="priceStore.current" class="flex items-baseline gap-2">
          <span class="text-base font-bold text-zinc-100 font-mono tabular-nums">
            <NumberTicker :value="formattedPrice" />
          </span>
          <span v-if="priceStore.change24h !== null" :class="['text-xs font-semibold font-mono transition-colors', priceColor]">
            <NumberTicker :value="formattedChange" />
          </span>
        </div>
        <div v-else class="text-sm text-zinc-600 italic">Connecting…</div>
      </div>
    </div>

    <!-- Right: portfolio -->
    <div v-if="portfolioStore.portfolio" class="flex items-center gap-3">
      <span class="text-xs text-zinc-500">Portfolio</span>
      <span class="text-sm font-semibold font-mono text-zinc-100 tabular-nums">
        <NumberTicker :value="formattedPortfolio" />
      </span>
      <div
        v-if="portfolioStore.portfolio?.roi_pct !== null && portfolioStore.portfolio !== null"
        :class="[
          'px-2 py-0.5 rounded-sm text-xs font-semibold font-mono tabular-nums border',
          (portfolioStore.portfolio?.roi_pct ?? 0) >= 0
            ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
            : 'text-rose-400 bg-rose-500/10 border-rose-500/20'
        ]"
      >
        <NumberTicker :value="formattedRoi" />
      </div>
    </div>
  </header>
</template>
