<script setup lang="ts">
import type { Trade } from '@/api/types'
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { formatDate, currencyCode, currencySymbol } from '@/utils/format'

const props = defineProps<{ trade: Trade }>()
const settingsStore = useSettingsStore()

const isBuy = computed(() => props.trade.action === 'BUY')
const quoteCurrency = computed(() => currencyCode(settingsStore.settings['quote_currency']))
const quoteSymbol = computed(() => currencySymbol(quoteCurrency.value))
</script>

<template>
  <div class="flex items-center justify-between gap-4 rounded-xl border border-slate-700/45 bg-slate-950/25 px-4 py-3 transition hover:border-slate-500/50 hover:bg-slate-900/45">
    <div class="flex min-w-0 items-center gap-4">
      <span :class="isBuy ? 'badge-buy' : 'badge-sell'">{{ trade.action }}</span>
      <div class="min-w-0">
        <div class="font-mono text-sm font-semibold tabular-nums text-slate-100">
          {{ trade.xrp_amount.toFixed(4) }} XRP
        </div>
        <div class="mt-0.5 font-mono text-xs tabular-nums text-slate-500">
          @ {{ quoteSymbol }}{{ trade.price_at_trade.toFixed(6) }}
        </div>
      </div>
    </div>

    <div class="flex-shrink-0 text-right">
      <div class="font-mono text-sm font-semibold tabular-nums text-slate-100">{{ quoteSymbol }}{{ trade.usd_amount.toFixed(2) }}</div>
      <div class="mt-0.5 text-xs text-slate-500">{{ formatDate(trade.timestamp) }}</div>
    </div>
  </div>
</template>
