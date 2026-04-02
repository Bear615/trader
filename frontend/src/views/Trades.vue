<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useTradesStore } from '@/stores/trades'
import api from '@/api/client'

const store = useTradesStore()
const totalPages = computed(() => Math.ceil(store.total / store.perPage))

onMounted(() => store.fetchTrades(1))

function setFilter(f: 'BUY' | 'SELL' | null) {
  store.actionFilter = f
  store.fetchTrades(1)
}

function nextPage() {
  if (store.page < totalPages.value) store.fetchTrades(store.page + 1)
}
function prevPage() {
  if (store.page > 1) store.fetchTrades(store.page - 1)
}

async function exportCsv() {
  const res = await api.get('/admin/export/trades', { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'trades.csv'
  a.click()
  URL.revokeObjectURL(url)
}

const pnlClass = (pnl: number | null) => {
  if (pnl === null) return 'text-gray-500'
  return pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
}

function fmt(ts: string) {
  return new Date(ts).toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  })
}
</script>

<template>
  <div class="space-y-5 max-w-[1400px]">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-gray-100">Trade History</h1>
        <p class="text-sm text-gray-500 mt-0.5">{{ store.total }} total trades</p>
      </div>
      <div class="flex items-center gap-3">
        <!-- Filter pills -->
        <div class="flex gap-1">
          <button
            @click="setFilter(null)"
            :class="['btn btn-sm', store.actionFilter === null ? 'btn-primary' : 'btn-ghost']"
          >All</button>
          <button
            @click="setFilter('BUY')"
            :class="['btn btn-sm', store.actionFilter === 'BUY'
              ? 'bg-emerald-700 hover:bg-emerald-600 text-white border-0'
              : 'btn-ghost']"
          >BUY</button>
          <button
            @click="setFilter('SELL')"
            :class="['btn btn-sm', store.actionFilter === 'SELL'
              ? 'bg-rose-700 hover:bg-rose-600 text-white border-0'
              : 'btn-ghost']"
          >SELL</button>
        </div>
        <!-- Export -->
        <button @click="exportCsv" class="btn btn-ghost btn-sm">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export CSV
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="table-wrapper">
      <table class="table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Action</th>
            <th class="text-right">XRP Amount</th>
            <th class="text-right">Price</th>
            <th class="text-right">USD Value</th>
            <th class="text-right">Fee</th>
            <th class="text-right">P&amp;L</th>
            <th>Trigger</th>
            <th class="text-right">USD After</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="store.loading">
            <td colspan="9" class="text-center py-10">
              <div class="inline-block w-5 h-5 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
            </td>
          </tr>
          <tr v-else-if="store.items.length === 0">
            <td colspan="9" class="text-center py-10 text-gray-600 italic">No trades yet</td>
          </tr>
          <template v-else>
            <tr v-for="trade in store.items" :key="trade.id">
              <td class="text-gray-500 text-xs font-mono">{{ fmt(trade.timestamp) }}</td>
              <td>
                <span :class="trade.action === 'BUY' ? 'badge-buy' : 'badge-sell'">{{ trade.action }}</span>
              </td>
              <td class="text-right font-mono tabular-nums">{{ trade.xrp_amount.toFixed(6) }}</td>
              <td class="text-right font-mono tabular-nums">${{ trade.price_at_trade.toFixed(6) }}</td>
              <td class="text-right font-mono tabular-nums">${{ trade.usd_amount.toFixed(2) }}</td>
              <td class="text-right font-mono tabular-nums text-gray-500">${{ trade.fee_usd.toFixed(4) }}</td>
              <td :class="['text-right font-mono tabular-nums', pnlClass(trade.pnl)]">
                {{ trade.pnl !== null ? (trade.pnl >= 0 ? '+$' : '-$') + Math.abs(trade.pnl).toFixed(4) : '—' }}
              </td>
              <td>
                <span :class="trade.triggered_by === 'ai' ? 'badge-ai' : 'badge text-gray-400 bg-gray-500/10 border-gray-500/25'">
                  {{ trade.triggered_by.toUpperCase() }}
                </span>
              </td>
              <td class="text-right font-mono tabular-nums text-gray-400">${{ trade.usd_balance_after?.toFixed(2) ?? '—' }}</td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-gray-500">
        Page {{ store.page }} of {{ totalPages }} · {{ store.total }} trades
      </p>
      <div class="flex gap-2">
        <button @click="prevPage" :disabled="store.page === 1" class="btn btn-ghost btn-sm">← Prev</button>
        <button @click="nextPage" :disabled="store.page === totalPages" class="btn btn-ghost btn-sm">Next →</button>
      </div>
    </div>
  </div>
</template>
