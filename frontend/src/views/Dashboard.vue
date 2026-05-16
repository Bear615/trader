<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { usePriceStore } from '@/stores/price'
import { usePortfolioStore } from '@/stores/portfolio'
import { useTradesStore } from '@/stores/trades'
import { useAIStore } from '@/stores/ai'
import { useSettingsStore } from '@/stores/settings'
import PriceChart from '@/components/PriceChart.vue'
import AIDecisionCard from '@/components/AIDecisionCard.vue'
import TradeRow from '@/components/TradeRow.vue'
import { currencyCode, formatCurrency, formatNumber, formatPercent } from '@/utils/format'

const priceStore = usePriceStore()
const portfolioStore = usePortfolioStore()
const tradesStore = useTradesStore()
const aiStore = useAIStore()
const settingsStore = useSettingsStore()

const timeframe = ref(String(settingsStore.settings['ui_chart_default_timeframe'] || '24h'))
const timeframes = ['1h', '6h', '24h', '7d', '30d']

async function loadAll() {
  await Promise.all([
    priceStore.fetchHistory(timeframe.value),
    portfolioStore.fetchPortfolio(),
    portfolioStore.fetchMetrics(),
    tradesStore.fetchTrades(1),
    aiStore.fetchDecisions(1),
  ])
}

onMounted(() => {
  loadAll()
  tradesStore.connectWebSocket()
  aiStore.connectWebSocket()
})

watch(timeframe, () => priceStore.fetchHistory(timeframe.value))

const p = computed(() => portfolioStore.portfolio)
const m = computed(() => portfolioStore.metrics)
const quoteCurrency = computed(() => currencyCode(m.value?.quote_currency, p.value?.quote_currency))
const currentPair = computed(() => `XRP / ${quoteCurrency.value}`)
const isLiveMode = computed(() => settingsStore.settings['trading_mode'] === 'live')

const portfolioTotal = computed(() =>
  p.value?.total_value_usd ?? m.value?.total_value_usd ?? p.value?.xrp_value_quote ?? m.value?.xrp_value_quote ?? 0,
)
const xrpValueRaw = computed(() => p.value?.xrp_value_quote ?? m.value?.xrp_value_quote ?? 0)
const quoteBalanceRaw = computed(() => p.value?.usd_balance ?? m.value?.usd_balance ?? 0)
const portfolioValue = computed(() => formatCurrency(portfolioTotal.value, quoteCurrency.value, 2))
const quoteBalance = computed(() => formatCurrency(quoteBalanceRaw.value, quoteCurrency.value, 2))
const xrpBalance = computed(() => formatNumber(p.value?.xrp_balance ?? m.value?.xrp_balance ?? 0, 4))
const xrpValue = computed(() => formatCurrency(xrpValueRaw.value, quoteCurrency.value, 2))
const totalTrades = computed(() => m.value?.total_trades ?? tradesStore.total ?? 0)
const winRate = computed(() => formatPercent(m.value?.win_rate_pct, 1))
const winRateGood = computed(() => (m.value?.win_rate_pct ?? 0) >= 50)
const averageEntry = computed(() => m.value?.avg_buy_price ? formatCurrency(m.value.avg_buy_price, quoteCurrency.value, 4) : '-')
const roiPct = computed(() => p.value?.roi_pct ?? m.value?.roi_pct ?? null)
const roiPositive = computed(() => (roiPct.value ?? 0) >= 0)
const roiLabel = computed(() => formatPercent(roiPct.value, 2, true))
const currentPrice = computed(() => priceStore.current ? formatCurrency(priceStore.current.price, quoteCurrency.value, 6) : '-')
const cashShare = computed(() => portfolioTotal.value > 0 ? quoteBalanceRaw.value / portfolioTotal.value * 100 : 0)
const latestDecision = computed(() => aiStore.items[0])
</script>

<template>
  <div class="view-shell">
    <div class="mobile-screen-header">
      <div>
        <p class="view-kicker">XRP AI Trader</p>
        <h1 class="view-title">Dashboard</h1>
        <p class="view-subtitle">Live XRP/{{ quoteCurrency }} account health and trading flow.</p>
      </div>
      <span class="app-chip" :class="isLiveMode ? 'border-rose-400/30 text-rose-300' : 'app-chip-active'">
        {{ isLiveMode ? 'Live' : 'Paper' }}
      </span>
    </div>

    <section class="panel space-y-4 p-4">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-xs font-semibold uppercase text-slate-500">XRP / {{ quoteCurrency }}</p>
          <div class="mt-1 font-mono text-3xl font-bold tabular-nums text-slate-50 md:text-4xl">
            {{ currentPrice }}
          </div>
          <p class="mt-1 text-xs text-slate-500">
            {{ priceStore.current ? 'Updated from the live feed' : 'Waiting for the next price poll' }}
          </p>
        </div>
        <div class="rounded-md border border-emerald-400/25 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-300">
          {{ priceStore.connected ? 'Live feed' : 'Offline' }}
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div class="card-sm">
          <div class="stat-label">Portfolio</div>
          <div class="mt-1 font-mono text-xl font-bold tabular-nums text-slate-50">{{ portfolioValue }}</div>
          <div class="mt-1 text-xs" :class="roiPositive ? 'text-emerald-400' : 'text-rose-400'">{{ roiLabel }} ROI</div>
        </div>
        <div class="card-sm">
          <div class="stat-label">{{ quoteCurrency }} Cash</div>
          <div class="mt-1 font-mono text-xl font-bold tabular-nums text-slate-50">{{ quoteBalance }}</div>
          <div class="mt-1 text-xs text-slate-500">{{ cashShare.toFixed(0) }}% liquid</div>
        </div>
        <div class="card-sm">
          <div class="stat-label">Open XRP</div>
          <div class="mt-1 font-mono text-xl font-bold tabular-nums text-slate-50">{{ xrpBalance }}</div>
          <div class="mt-1 text-xs text-slate-500">{{ xrpValue }}</div>
        </div>
        <div class="card-sm">
          <div class="stat-label">Win Rate</div>
          <div class="mt-1 font-mono text-xl font-bold tabular-nums" :class="winRateGood ? 'text-emerald-400' : 'text-rose-400'">
            {{ winRate }}
          </div>
          <div class="mt-1 text-xs text-slate-500">{{ totalTrades }} trades</div>
        </div>
      </div>
    </section>

    <section class="panel p-4 md:p-5">
      <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="section-title">{{ currentPair }}</h2>
          <p class="section-subtitle mt-1">Price action with mobile-safe timeframe controls.</p>
        </div>
        <div class="segmented overflow-x-auto">
          <button
            v-for="tf in timeframes"
            :key="tf"
            @click="timeframe = tf"
            class="segmented-button"
            :class="{ 'segmented-button-active': timeframe === tf }"
          >
            {{ tf.toUpperCase() }}
          </button>
        </div>
      </div>
      <PriceChart :data="priceStore.history" :loading="priceStore.loading" :quote-currency="quoteCurrency" />
    </section>

    <section class="grid grid-cols-1 gap-3 md:grid-cols-3">
      <div class="card-sm">
        <div class="stat-label">Average Entry</div>
        <div class="mt-1 font-mono text-lg font-bold tabular-nums text-slate-50">{{ averageEntry }}</div>
        <div class="text-xs text-slate-500">Per XRP</div>
      </div>
      <div class="card-sm">
        <div class="stat-label">Latest AI</div>
        <div class="mt-1 flex items-center justify-between gap-3">
          <span :class="latestDecision?.action === 'BUY' ? 'badge-buy' : latestDecision?.action === 'SELL' ? 'badge-sell' : 'badge-hold'">
            {{ latestDecision?.action ?? 'WAIT' }}
          </span>
          <span class="font-mono text-sm text-slate-300">
            {{ latestDecision ? Math.round(latestDecision.confidence * 100) + '%' : '-' }}
          </span>
        </div>
      </div>
    </section>

    <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <section class="panel p-4 md:p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="section-title">Recent Trades</h2>
          <RouterLink to="/trades" class="text-sm font-medium text-blue-400 hover:text-blue-300">View all</RouterLink>
        </div>
        <div v-if="tradesStore.items.length === 0" class="mobile-list-card py-10 text-center text-sm text-slate-500">
          No trades yet
        </div>
        <div v-else class="space-y-3">
          <TradeRow v-for="trade in tradesStore.items.slice(0, 4)" :key="trade.id" :trade="trade" />
        </div>
      </section>

      <section class="panel p-4 md:p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="section-title">AI Decisions</h2>
          <RouterLink to="/ai" class="text-sm font-medium text-blue-400 hover:text-blue-300">View all</RouterLink>
        </div>
        <div v-if="aiStore.items.length === 0" class="mobile-list-card py-10 text-center text-sm text-slate-500">
          No AI decisions yet
        </div>
        <div v-else class="space-y-2">
          <AIDecisionCard
            v-for="decision in aiStore.items.slice(0, 5)"
            :key="decision.id"
            :decision="decision"
            compact
          />
        </div>
      </section>
    </div>
  </div>
</template>
