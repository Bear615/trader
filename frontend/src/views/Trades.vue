<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useTradesStore } from '@/stores/trades'
import { useSettingsStore } from '@/stores/settings'
import { currencyCode, formatCurrency, formatDate, formatNumber } from '@/utils/format'
import api from '@/api/client'

const store = useTradesStore()
const settingsStore = useSettingsStore()
const expandedTradeId = ref<number | null>(null)
const exportAnimating = ref(false)

const totalPages = computed(() => Math.ceil(store.total / store.perPage))
const quoteCurrency = computed(() => currencyCode(settingsStore.settings['quote_currency']))
const visiblePnl = computed(() => store.items.reduce((sum, trade) => sum + (trade.pnl ?? 0), 0))
const visiblePnlClass = computed(() => visiblePnl.value >= 0 ? 'text-emerald-400' : 'text-rose-400')
const buyCount = computed(() => store.items.filter((trade) => trade.action === 'BUY').length)
const sellCount = computed(() => store.items.filter((trade) => trade.action === 'SELL').length)

onMounted(() => store.fetchTrades(1))

function setFilter(f: 'BUY' | 'SELL' | null) {
  store.actionFilter = f
  store.fetchTrades(1)
  expandedTradeId.value = null
}

function nextPage() {
  if (store.page < totalPages.value) store.fetchTrades(store.page + 1)
}

function prevPage() {
  if (store.page > 1) store.fetchTrades(store.page - 1)
}

async function exportCsv() {
  if (exportAnimating.value) return
  exportAnimating.value = true
  const res = await api.get('/admin/export/trades', { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `xrp-${quoteCurrency.value.toLowerCase()}-trades.csv`
  a.click()
  URL.revokeObjectURL(url)
  window.setTimeout(() => {
    exportAnimating.value = false
  }, 1100)
}

function pnlLabel(pnl: number | null) {
  if (pnl === null) return '-'
  return formatCurrency(Math.abs(pnl), quoteCurrency.value, 4).replace(/^/, pnl >= 0 ? '+' : '-')
}

function pnlClass(pnl: number | null) {
  if (pnl === null) return 'text-slate-500'
  return pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
}

function toggleTrade(id: number) {
  expandedTradeId.value = expandedTradeId.value === id ? null : id
}
</script>

<template>
  <div class="view-shell">
    <div class="mobile-screen-header">
      <div>
        <p class="view-kicker">Audit log</p>
        <h1 class="view-title">Trades</h1>
        <p class="view-subtitle">History as scan-friendly cards, with table detail retained on desktop.</p>
      </div>
      <button @click="exportCsv" class="btn btn-ghost btn-sm shrink-0 overflow-hidden" :class="{ 'download-launch': exportAnimating }">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0l-4-4m4 4l4-4M5 19h14" />
        </svg>
        Export
        <span aria-hidden="true" class="download-orb" />
      </button>
    </div>

    <section class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <div class="card-sm">
        <div class="stat-label">Total Trades</div>
        <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-slate-50">{{ store.total }}</div>
        <div class="text-xs text-slate-500">All time</div>
      </div>
      <div class="card-sm">
        <div class="stat-label">Visible P&amp;L</div>
        <div class="mt-1 font-mono text-2xl font-bold tabular-nums" :class="visiblePnlClass">
          {{ pnlLabel(visiblePnl) }}
        </div>
        <div class="text-xs text-slate-500">This page</div>
      </div>
      <div class="card-sm">
        <div class="stat-label">Buys</div>
        <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-emerald-400">{{ buyCount }}</div>
        <div class="text-xs text-slate-500">Visible</div>
      </div>
      <div class="card-sm">
        <div class="stat-label">Sells</div>
        <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-rose-400">{{ sellCount }}</div>
        <div class="text-xs text-slate-500">Visible</div>
      </div>
    </section>

    <div class="sticky-mobile-action flex items-center justify-between gap-3">
      <div class="segmented">
        <button @click="setFilter(null)" class="segmented-button" :class="{ 'segmented-button-active': store.actionFilter === null }">All</button>
        <button @click="setFilter('BUY')" class="segmented-button" :class="{ 'segmented-button-active': store.actionFilter === 'BUY' }">Buy</button>
        <button @click="setFilter('SELL')" class="segmented-button" :class="{ 'segmented-button-active': store.actionFilter === 'SELL' }">Sell</button>
      </div>
      <span class="hidden text-xs text-slate-500 sm:block">XRP/{{ quoteCurrency }}</span>
    </div>

    <section class="panel p-4 md:hidden">
      <div v-if="store.loading" class="flex justify-center py-12">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
      </div>
      <div v-else-if="store.items.length === 0" class="py-12 text-center text-sm text-slate-500">
        No trades yet
      </div>
      <div v-else class="space-y-3">
        <article
          v-for="trade in store.items"
          :key="trade.id"
          class="mobile-list-card"
        >
          <button class="w-full text-left" @click="toggleTrade(trade.id)">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span :class="trade.action === 'BUY' ? 'badge-buy' : 'badge-sell'">{{ trade.action }}</span>
                  <span :class="trade.triggered_by === 'ai' ? 'badge-ai' : 'badge-hold'">{{ trade.triggered_by }}</span>
                </div>
                <div class="mt-2 font-mono text-lg font-bold tabular-nums text-slate-50">
                  {{ formatNumber(trade.xrp_amount, 4) }} XRP
                </div>
                <div class="mt-1 text-xs text-slate-500">{{ formatDate(trade.timestamp) }}</div>
              </div>
              <div class="text-right">
                <div class="font-mono text-sm font-semibold tabular-nums text-slate-100">
                  {{ formatCurrency(trade.usd_amount, quoteCurrency, 2) }}
                </div>
                <div class="mt-1 font-mono text-xs tabular-nums" :class="pnlClass(trade.pnl)">
                  {{ pnlLabel(trade.pnl) }}
                </div>
              </div>
            </div>
          </button>

          <div v-if="expandedTradeId === trade.id" class="mt-3 border-t border-slate-800/75 pt-2">
            <div class="mobile-detail-row">
              <span class="mobile-detail-label">Price</span>
              <span class="mobile-detail-value">{{ formatCurrency(trade.price_at_trade, quoteCurrency, 6) }}</span>
            </div>
            <div class="mobile-detail-row">
              <span class="mobile-detail-label">Fee</span>
              <span class="mobile-detail-value">{{ formatCurrency(trade.fee_usd, quoteCurrency, 4) }}</span>
            </div>
            <div class="mobile-detail-row">
              <span class="mobile-detail-label">{{ quoteCurrency }} After</span>
              <span class="mobile-detail-value">{{ formatCurrency(trade.usd_balance_after, quoteCurrency, 2) }}</span>
            </div>
            <div class="mobile-detail-row">
              <span class="mobile-detail-label">XRP After</span>
              <span class="mobile-detail-value">{{ formatNumber(trade.xrp_balance_after, 4) }}</span>
            </div>
            <p v-if="trade.note" class="mt-3 text-xs leading-relaxed text-slate-400">{{ trade.note }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="panel hidden p-0 md:block">
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
                  <div class="text-slate-100">{{ formatDate(trade.timestamp) }}</div>
                </td>
                <td>
                  <span :class="trade.action === 'BUY' ? 'badge-buy' : 'badge-sell'">{{ trade.action }}</span>
                </td>
                <td class="text-right font-mono tabular-nums">{{ formatNumber(trade.xrp_amount, 6) }}</td>
                <td class="text-right font-mono tabular-nums">{{ formatCurrency(trade.price_at_trade, quoteCurrency, 6) }}</td>
                <td class="text-right font-mono tabular-nums">{{ formatCurrency(trade.usd_amount, quoteCurrency, 2) }}</td>
                <td class="text-right font-mono tabular-nums text-slate-500">{{ formatCurrency(trade.fee_usd, quoteCurrency, 4) }}</td>
                <td :class="['text-right font-mono tabular-nums', pnlClass(trade.pnl)]">{{ pnlLabel(trade.pnl) }}</td>
                <td>
                  <span :class="trade.triggered_by === 'ai' ? 'badge-ai' : 'badge-hold'">{{ trade.triggered_by.toUpperCase() }}</span>
                </td>
                <td class="text-right font-mono tabular-nums text-slate-400">
                  {{ formatCurrency(trade.usd_balance_after, quoteCurrency, 2) }}
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-sm text-slate-500">
        Page {{ store.page }} of {{ totalPages }}
      </p>
      <div class="flex gap-2">
        <button @click="prevPage" :disabled="store.page === 1" class="btn btn-ghost btn-sm">Prev</button>
        <button @click="nextPage" :disabled="store.page === totalPages" class="btn btn-ghost btn-sm">Next</button>
      </div>
    </div>
  </div>
</template>
