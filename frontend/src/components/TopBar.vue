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

const marketStatus = computed(() => priceStore.connected ? 'Live price' : 'Feed offline')
</script>

<template>
  <header class="flex min-h-[68px] flex-shrink-0 items-center border-b border-slate-800/80 bg-[#070b10]/94 px-4 pt-[env(safe-area-inset-top)] backdrop-blur md:min-h-[73px] md:px-8">
    <div class="flex w-full items-center justify-between gap-3">
      <div class="min-w-0">
        <div class="flex items-center gap-2 text-xs font-semibold text-slate-400">
          <span class="text-slate-200">XRP/{{ quoteCurrency }}</span>
          <span class="h-1 w-1 rounded-full bg-slate-600" />
          <span class="flex items-center gap-1.5" :class="isLiveMode ? 'text-rose-300' : 'text-amber-300'">
            <span class="h-1.5 w-1.5 rounded-full" :class="isLiveMode ? 'bg-rose-400' : 'bg-amber-400'" />
            {{ isLiveMode ? 'LIVE' : 'PAPER' }}
          </span>
        </div>
        <div class="mt-1 truncate text-xl font-bold text-slate-50 md:text-2xl">
          <NumberTicker :value="formattedPrice" />
        </div>
      </div>

      <div class="flex flex-col items-end gap-1">
        <div class="app-chip" :class="priceStore.connected ? 'border-emerald-400/25 text-emerald-300' : 'border-rose-400/25 text-rose-300'">
          <span class="status-dot" :class="priceStore.connected ? 'bg-emerald-400' : 'bg-rose-400'" />
          {{ marketStatus }}
        </div>
        <div class="hidden text-[11px] text-slate-500 sm:block">Quote: {{ quoteCurrency }}</div>
      </div>
    </div>
  </header>
</template>
