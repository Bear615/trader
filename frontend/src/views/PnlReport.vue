<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/api/client'
import type { PnlReport } from '@/api/types'
import { useSettingsStore } from '@/stores/settings'
import { currencyCode, formatCurrency, formatDate, formatNumber, formatPercent } from '@/utils/format'

const settingsStore = useSettingsStore()
const report = ref<PnlReport | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const quoteCurrency = computed(() => currencyCode(settingsStore.settings['quote_currency']))
const winRate = computed(() => {
  if (!report.value?.trade_count) return 0
  return report.value.win_count / report.value.trade_count * 100
})
const largestWinner = computed(() => Math.max(0, ...((report.value?.items ?? []).map((trade) => trade.pnl ?? 0))))
const largestLoser = computed(() => Math.min(0, ...((report.value?.items ?? []).map((trade) => trade.pnl ?? 0))))
const resetLabel = computed(() => report.value?.reset_at ? new Date(report.value.reset_at).toLocaleString() : 'All-time calculator')

onMounted(loadReport)

async function loadReport() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get<PnlReport>('/trades/pnl-report')
    report.value = res.data
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to load the P&L report.'
  } finally {
    loading.value = false
  }
}

function pnlLabel(pnl: number | null) {
  if (pnl === null) return '-'
  return formatCurrency(Math.abs(pnl), quoteCurrency.value, 4).replace(/^/, pnl >= 0 ? '+' : '-')
}

function pnlClass(pnl: number | null) {
  if (pnl === null) return 'text-slate-500'
  return pnl >= 0 ? 'text-emerald-300' : 'text-rose-300'
}
</script>

<template>
  <div class="view-shell pnl-report-shell">
    <div class="mobile-screen-header">
      <div>
        <p class="view-kicker">P&amp;L calculator</p>
        <h1 class="view-title">Trade Profit Report</h1>
        <p class="view-subtitle">A clean breakdown of which sell trades earned profit after the current reset baseline.</p>
      </div>
      <button class="btn btn-ghost btn-sm" :disabled="loading" @click="loadReport">
        {{ loading ? 'Refreshing…' : 'Refresh' }}
      </button>
    </div>

    <section class="pnl-hero panel">
      <div>
        <p class="view-kicker">Realized since</p>
        <h2 class="mt-1 text-xl font-semibold text-slate-50">{{ resetLabel }}</h2>
      </div>
      <div class="text-left md:text-right">
        <p class="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Net realized</p>
        <div class="mt-1 font-mono text-4xl font-bold tabular-nums md:text-5xl" :class="(report?.realized_pnl_usd ?? 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'">
          {{ pnlLabel(report?.realized_pnl_usd ?? 0) }}
        </div>
      </div>
    </section>

    <div v-if="error" class="panel border-rose-400/30 bg-rose-500/10 text-sm text-rose-200">
      {{ error }}
    </div>

    <section class="grid grid-cols-2 gap-3 md:grid-cols-5">
      <div class="card-sm pnl-stat-card">
        <div class="stat-label">Winning P&amp;L</div>
        <div class="mt-1 font-mono text-xl font-bold text-emerald-300">{{ pnlLabel(report?.winning_pnl_usd ?? 0) }}</div>
      </div>
      <div class="card-sm pnl-stat-card">
        <div class="stat-label">Losing P&amp;L</div>
        <div class="mt-1 font-mono text-xl font-bold text-rose-300">{{ pnlLabel(report?.losing_pnl_usd ?? 0) }}</div>
      </div>
      <div class="card-sm pnl-stat-card">
        <div class="stat-label">Closed Sells</div>
        <div class="mt-1 font-mono text-xl font-bold text-slate-50">{{ report?.trade_count ?? 0 }}</div>
      </div>
      <div class="card-sm pnl-stat-card">
        <div class="stat-label">Win Rate</div>
        <div class="mt-1 font-mono text-xl font-bold text-blue-200">{{ formatPercent(winRate, 1) }}</div>
      </div>
      <div class="card-sm pnl-stat-card col-span-2 md:col-span-1">
        <div class="stat-label">Best / Worst</div>
        <div class="mt-1 font-mono text-sm font-bold text-slate-50">{{ pnlLabel(largestWinner) }} / {{ pnlLabel(largestLoser) }}</div>
      </div>
    </section>

    <section class="panel p-3 md:p-5">
      <div v-if="loading" class="flex justify-center py-16">
        <div class="h-7 w-7 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
      </div>
      <div v-else-if="!report?.items.length" class="py-16 text-center">
        <p class="text-base font-semibold text-slate-200">No realized P&amp;L yet</p>
        <p class="mt-1 text-sm text-slate-500">Sell trades after the reset baseline will appear here.</p>
      </div>
      <div v-else class="space-y-3">
        <article v-for="trade in report.items" :key="trade.id" class="pnl-report-row">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <span class="badge-sell">SELL</span>
                <span :class="trade.triggered_by === 'ai' ? 'badge-ai' : 'badge-hold'">{{ trade.triggered_by.toUpperCase() }}</span>
              </div>
              <h3 class="mt-3 font-mono text-lg font-bold text-slate-50">{{ formatNumber(trade.xrp_amount, 4) }} XRP</h3>
              <p class="mt-1 text-xs text-slate-500">{{ formatDate(trade.timestamp) }}</p>
            </div>
            <div class="text-right">
              <p class="font-mono text-2xl font-bold tabular-nums" :class="pnlClass(trade.pnl)">{{ pnlLabel(trade.pnl) }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ formatCurrency(trade.usd_amount, quoteCurrency, 2) }} closed</p>
            </div>
          </div>
          <div class="mt-4 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
            <div class="pnl-row-chip"><span>Price</span><strong>{{ formatCurrency(trade.price_at_trade, quoteCurrency, 6) }}</strong></div>
            <div class="pnl-row-chip"><span>Fee</span><strong>{{ formatCurrency(trade.fee_usd, quoteCurrency, 4) }}</strong></div>
            <div class="pnl-row-chip"><span>{{ quoteCurrency }} After</span><strong>{{ formatCurrency(trade.usd_balance_after, quoteCurrency, 2) }}</strong></div>
            <div class="pnl-row-chip"><span>XRP After</span><strong>{{ formatNumber(trade.xrp_balance_after, 4) }}</strong></div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
