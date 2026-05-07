<script setup lang="ts">
import type { Trade } from '@/api/types'
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { currencyCode, formatCurrency, formatDate, formatNumber } from '@/utils/format'

const props = defineProps<{ trade: Trade }>()
const settingsStore = useSettingsStore()

const isBuy = computed(() => props.trade.action === 'BUY')
const quoteCurrency = computed(() => currencyCode(settingsStore.settings['quote_currency']))
</script>

<template>
  <div class="flex items-center justify-between gap-4 rounded-lg border border-slate-700/45 bg-slate-950/25 px-4 py-3 transition hover:border-slate-500/50 hover:bg-slate-900/45">
    <div class="flex min-w-0 items-center gap-4">
      <span :class="isBuy ? 'badge-buy' : 'badge-sell'">{{ trade.action }}</span>
      <div class="min-w-0">
        <div class="font-mono text-sm font-semibold tabular-nums text-slate-100">
          {{ formatNumber(trade.xrp_amount, 4) }} XRP
        </div>
        <div class="mt-0.5 font-mono text-xs tabular-nums text-slate-500">
          @ {{ formatCurrency(trade.price_at_trade, quoteCurrency, 6) }}
        </div>
      </div>
    </div>

    <div class="flex-shrink-0 text-right">
      <div class="font-mono text-sm font-semibold tabular-nums text-slate-100">{{ formatCurrency(trade.usd_amount, quoteCurrency, 2) }}</div>
      <div class="mt-0.5 text-xs text-slate-500">{{ formatDate(trade.timestamp) }}</div>
    </div>
  </div>
</template>
