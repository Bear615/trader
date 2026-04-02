<script setup lang="ts">
import type { Trade } from '@/api/types'
import { computed } from 'vue'
import { formatDate } from '@/utils/format'

const props = defineProps<{ trade: Trade }>()

const isBuy = computed(() => props.trade.action === 'BUY')
</script>

<template>
  <div class="flex items-center justify-between py-2.5 px-3 rounded-lg bg-surface-900 border border-surface-700 hover:border-surface-600 hover:-translate-y-px hover:shadow-lg hover:shadow-black/30 transition-all duration-150">
    <div class="flex items-center gap-3 min-w-0">
      <span :class="isBuy ? 'badge-buy' : 'badge-sell'">{{ trade.action }}</span>
      <div class="min-w-0">
        <div class="text-sm font-medium text-gray-200 font-mono tabular-nums">
          {{ trade.xrp_amount.toFixed(4) }} XRP
        </div>
        <div class="text-xs text-gray-500 font-mono">@ ${{ trade.price_at_trade.toFixed(6) }}</div>
      </div>
    </div>
    <div class="text-right flex-shrink-0">
      <div class="text-sm font-mono text-gray-300 tabular-nums">${{ trade.usd_amount.toFixed(2) }}</div>
      <div class="text-xs text-gray-600">{{ formatDate(trade.timestamp) }}</div>
    </div>
  </div>
</template>
