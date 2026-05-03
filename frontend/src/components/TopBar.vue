<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePriceStore } from '@/stores/price'
import { usePortfolioStore } from '@/stores/portfolio'
import { useSettingsStore } from '@/stores/settings'
import NumberTicker from './NumberTicker.vue'
import { currencySymbol, currencyCode } from '@/utils/format'

const priceStore = usePriceStore()
const portfolioStore = usePortfolioStore()
const settingsStore = useSettingsStore()

onMounted(() => portfolioStore.fetchPortfolio())

const isLiveMode = computed(() => settingsStore.settings['trading_mode'] === 'live')
const quoteCurrency = computed(() => currencyCode(settingsStore.settings['quote_currency'], portfolioStore.portfolio?.quote_currency))
const quoteSymbol = computed(() => currencySymbol(quoteCurrency.value))

const formattedPrice = computed(() =>
  priceStore.current ? quoteSymbol.value + priceStore.current.price.toFixed(6) : 'Waiting for price'
)

const marketStatus = computed(() => priceStore.connected ? 'Market Open' : 'Feed Offline')
</script>

<template>
  <header class="flex min-h-[73px] flex-shrink-0 items-center border-b border-slate-800/70 bg-[#01040a]/82 px-5 backdrop-blur-xl md:px-8">
    <div class="flex w-full items-center justify-between gap-4">
      <div class="flex min-w-0 items-center gap-5 text-sm md:text-base">
        <div class="font-semibold text-slate-300">XRP/{{ quoteCurrency }}</div>
        <div class="h-7 w-px bg-slate-700/70" />
        <div class="flex items-center gap-2 font-bold text-amber-300">
          <span class="h-2 w-2 rounded-full bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.7)]" />
          {{ isLiveMode ? 'LIVE' : 'PAPER' }}
        </div>
        <div class="truncate text-lg font-bold tracking-[-0.02em] text-slate-50 md:text-xl">
          <NumberTicker :value="formattedPrice" />
        </div>
      </div>

      <div class="status-pill hidden sm:inline-flex">
        <span class="status-dot" :class="priceStore.connected ? 'bg-emerald-400' : 'bg-rose-400'" />
        {{ marketStatus }}
      </div>
    </div>
  </header>
</template>
