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
  <header class="h-20 flex items-center justify-between px-8 bg-black/20 backdrop-blur-3xl border-b border-white/[0.08] shadow-[0_4px_30px_rgba(0,0,0,0.1)] flex-shrink-0 sticky top-0 z-30">
    <!-- Live price ticker -->
    <div class="flex items-center gap-5">
      <!-- Live / offline pill -->
      <div class="flex items-center gap-2">
        <span class="relative flex h-2 w-2">
          <span v-if="priceStore.connected" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span class="relative inline-flex rounded-full h-2 w-2" :class="priceStore.connected ? 'bg-emerald-400' : 'bg-gray-600'" />
        </span>
        <span class="text-xs font-medium" :class="priceStore.connected ? 'text-emerald-400' : 'text-gray-500'">
          {{ priceStore.connected ? 'LIVE' : 'OFFLINE' }}
        </span>
      </div>

      <!-- Trading mode badge -->
      <div v-if="isLiveMode" class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/15 border border-red-500/30">
        <span class="relative flex h-1.5 w-1.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
          <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-red-400" />
        </span>
        <span class="text-xs font-bold text-red-400 tracking-wide">LIVE</span>
      </div>
      <div v-else class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-500/10 border border-slate-500/20">
        <span class="text-xs font-semibold text-slate-500 tracking-wide">PAPER</span>
      </div>

      <div class="w-px h-5 bg-white/[0.12]" />

      <!-- Price -->
      <div class="flex items-center gap-3">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">XRP/USD</span>
        <div v-if="priceStore.current" class="flex items-baseline gap-2">
          <span class="text-xl font-bold text-gray-100 font-mono tabular-nums">
            <NumberTicker :value="formattedPrice" />
          </span>
          <span v-if="priceStore.change24h !== null" :class="['text-xs font-semibold font-mono transition-colors duration-300', priceColor]">
            <NumberTicker :value="formattedChange" />
          </span>
        </div>
        <div v-else class="text-sm text-gray-600 italic">Connecting…</div>
      </div>
    </div>

    <!-- Portfolio summary -->
    <div v-if="portfolioStore.portfolio" class="flex items-center gap-4">
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-500">Portfolio</span>
        <span class="text-sm font-semibold font-mono text-gray-100 tabular-nums">
          <NumberTicker :value="formattedPortfolio" />
        </span>
      </div>
      <div
        v-if="portfolioStore.portfolio?.roi_pct !== null && portfolioStore.portfolio !== null"
        :class="[
          'px-2.5 py-1 rounded-lg text-xs font-semibold font-mono tabular-nums border',
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
