<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useTradesStore } from '@/stores/trades'
import { useSettingsStore } from '@/stores/settings'
import { currencyCode, currencySymbol } from '@/utils/format'
import api from '@/api/client'

const store = useTradesStore()
const settingsStore = useSettingsStore()
const totalPages = computed(() => Math.ceil(store.total / store.perPage))
const quoteCurrency = computed(() => currencyCode(settingsStore.settings['quote_currency']))
const quoteSymbol = computed(() => currencySymbol(quoteCurrency.value))

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

const visiblePnl = computed(() => store.items.reduce((sum, trade) => sum + (trade.pnl ?? 0), 0))
const visiblePnlClass = computed(() => visiblePnl.value >= 0 ? 'text-emerald-400' : 'text-rose-400')
const pnlClass = (pnl: number | null) => {
  if (pnl === null) return 'text-slate-500'
  return pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
}

function fmtDate(ts: string) {
  const d = new Date(ts)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function fmtTime(ts: string) {
  const d = new Date(ts)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}
</script>

<template>
  <div class="view-shell">
    <div class="view-header">
      <div>
        <h1 class="view-title">Trade History</h1>
        <p class="view-subtitle">Review your past XRP/{{ quoteCurrency }} trades.</p>
      </div>

      <div class="flex flex-wrap items-center gap-4">
        <div class="segmented">
          <button @click="setFilter(null)" class="segmented-button" :class="{ 'segmented-button-active': store.actionFilter === null }">All</button>
          <button @click="setFilter('BUY')" class="segmented-button" :class="{ 'segmented-button-active': store.actionFilter === 'BUY' }">Buy</button>
          <button @click="setFilter('SELL')" class="segmented-button" :class="{ 'segmented-button-active': store.actionFilter === 'SELL' }">Sell</button>
        </div>

        <button @click="exportCsv" class="btn btn-ghost">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0l-4-4m4 4l4-4M5 19h14" />
          </svg>
          Export CSV
        </button>
      </div>
    </div>

    <div class="panel p-0">
      <div class="grid grid-cols-1 divide-y divide-slate-700/50 md:grid-cols-2 md:divide-x md:divide-y-0">
        <div class="flex items-center gap-5 p-8">
          <div class="flex h-14 w-14 items-center justify-center rounded-xl border border-slate-600/45 bg-slate-950/35 text-slate-300">
            <svg class="h-7 w-7" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h11m0 0l-4-4m4 4l-4 4M17 17H6m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>
          <div>
            <div class="text-sm text-slate-400">Total Trades</div>
            <div class="mt-1 text-3xl font-bold tabular-nums text-slate-50">{{ store.total }}</div>
            <div class="mt-1 text-sm text-slate-500">All time</div>
          </div>
        </div>

        <div class="flex items-center gap-5 p-8">
          <div class="flex h-14 w-14 items-center justify-center rounded-xl border border-slate-600/45 bg-slate-950/35 text-slate-300">
            <svg class="h-7 w-7" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 17l6-6 4 4 6-8" />
            </svg>
          </div>
          <div>
            <div class="text-sm text-slate-400">Realized P&amp;L</div>
            <div class="mt-1 text-3xl font-bold tabular-nums" :class="visiblePnlClass">
              {{ visiblePnl >= 0 ? '+' : '-' }}{{ quoteSymbol }}{{ Math.abs(visiblePnl).toFixed(4) }}
            </div>
            <div class="mt-1 text-sm text-slate-500">Visible trades</div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel p-0">
      <div class="table-wrapper border-0 bg-transparent shadow-none">
        <table class="table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Action</th>
              <th class="text-right">XRP Amount</th>
              <th class="text-right">Price ({{ quoteCurrency }})</th>
              <th class="text-right">Value ({{ quoteCurrency }})</th>
              <th class="text-right">Fee ({{ quoteCurrency }})</th>
              <th class="text-right">P&amp;L ({{ quoteCurrency }})</th>
              <th>Trigger</th>
              <th class="text-right">{{ quoteCurrency }} After</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="store.loading">
              <td colspan="9" class="py-12 text-center">
                <div class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
              </td>
            </tr>
            <tr v-else-if="store.items.length === 0">
              <td colspan="9" class="py-12 text-center text-slate-500">No trades yet</td>
            </tr>
            <template v-else>
              <tr v-for="trade in store.items" :key="trade.id">
                <td>
                  <div class="text-slate-100">{{ fmtDate(trade.timestamp) }}</div>
                  <div class="mt-1 font-mono text-xs text-slate-500">{{ fmtTime(trade.timestamp) }}</div>
                </td>
                <td>
                  <span :class="trade.action === 'BUY' ? 'badge-buy' : 'badge-sell'">{{ trade.action }}</span>
                </td>
                <td class="text-right font-mono tabular-nums">{{ trade.xrp_amount.toFixed(6) }}</td>
                <td class="text-right font-mono tabular-nums">{{ quoteSymbol }}{{ trade.price_at_trade.toFixed(6) }}</td>
                <td class="text-right font-mono tabular-nums">{{ quoteSymbol }}{{ trade.usd_amount.toFixed(2) }}</td>
                <td class="text-right font-mono tabular-nums text-slate-500">{{ quoteSymbol }}{{ trade.fee_usd.toFixed(4) }}</td>
                <td :class="['text-right font-mono tabular-nums', pnlClass(trade.pnl)]">
                  {{ trade.pnl !== null ? (trade.pnl >= 0 ? '+' : '-') + quoteSymbol + Math.abs(trade.pnl).toFixed(4) : '-' }}
                </td>
                <td>
                  <span :class="trade.triggered_by === 'ai' ? 'badge-ai' : 'badge border-slate-500/30 bg-slate-500/10 text-slate-300'">
                    {{ trade.triggered_by.toUpperCase() }}
                  </span>
                </td>
                <td class="text-right font-mono tabular-nums text-slate-400">
                  {{ trade.usd_balance_after != null ? quoteSymbol + trade.usd_balance_after.toFixed(2) : '-' }}
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-sm text-slate-500">
        Page {{ store.page }} of {{ totalPages }} / {{ store.total }} trades
      </p>
      <div class="flex gap-2">
        <button @click="prevPage" :disabled="store.page === 1" class="btn btn-ghost btn-sm">Prev</button>
        <button @click="nextPage" :disabled="store.page === totalPages" class="btn btn-ghost btn-sm">Next</button>
      </div>
    </div>
  </div>
</template>
