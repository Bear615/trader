<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { usePriceStore } from '@/stores/price'
import { usePortfolioStore } from '@/stores/portfolio'
import { useTradesStore } from '@/stores/trades'
import { useAIStore } from '@/stores/ai'
import PriceChart from '@/components/PriceChart.vue'
import AIDecisionCard from '@/components/AIDecisionCard.vue'
import TradeRow from '@/components/TradeRow.vue'
import { currencySymbol, currencyCode } from '@/utils/format'

const priceStore = usePriceStore()
const portfolioStore = usePortfolioStore()
const tradesStore = useTradesStore()
const aiStore = useAIStore()

const timeframe = ref('24h')
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
const quoteSymbol = computed(() => currencySymbol(quoteCurrency.value))
const currentPair = computed(() => `XRP / ${quoteCurrency.value}`)

function formatQuote(value: number | null | undefined, decimals = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return quoteSymbol.value + value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

function formatNumber(value: number | null | undefined, decimals = 4) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

const portfolioValue = computed(() => formatQuote(p.value?.xrp_value_quote ?? m.value?.xrp_value_quote ?? 0, 2))
const quoteBalance = computed(() => formatQuote(p.value?.usd_balance ?? m.value?.usd_balance ?? 0, 2))
const xrpBalance = computed(() => formatNumber(p.value?.xrp_balance ?? m.value?.xrp_balance ?? 0, 4))
const xrpValue = computed(() => formatQuote(p.value?.xrp_value_quote ?? m.value?.xrp_value_quote ?? 0, 2))
const totalTrades = computed(() => m.value?.total_trades ?? tradesStore.total ?? 0)
const winRate = computed(() => m.value?.win_rate_pct != null ? m.value.win_rate_pct.toFixed(1) + '%' : '-')
const winRateGood = computed(() => (m.value?.win_rate_pct ?? 0) >= 50)
const averageEntry = computed(() => m.value?.avg_buy_price ? formatQuote(m.value.avg_buy_price, 4) : '-')
const roiPct = computed(() => p.value?.roi_pct ?? m.value?.roi_pct ?? null)
const roiPositive = computed(() => (roiPct.value ?? 0) >= 0)
const roiLabel = computed(() => roiPct.value !== null ? (roiPositive.value ? '+' : '') + roiPct.value.toFixed(2) + '%' : '-')
</script>

<template>
  <div class="view-shell">
    <div class="view-header">
      <div>
        <h1 class="view-title">Dashboard</h1>
        <p class="view-subtitle">XRP / XRP-{{ quoteCurrency }} trading overview using live account and price data.</p>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 xl:grid-cols-5">
      <div class="metric-card">
        <div class="metric-top">
          <div class="metric-icon">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 7.5h14a2 2 0 012 2v9a2 2 0 01-2 2H4a2 2 0 01-2-2v-9a2 2 0 012-2zm0 0V5.5a2 2 0 012-2h10" />
            </svg>
          </div>
          <span>Portfolio Value</span>
        </div>
        <div>
          <div class="metric-value">{{ portfolioValue }}</div>
          <div class="metric-sub">
            <span :class="roiPositive ? 'text-emerald-400' : 'text-rose-400'">{{ roiLabel }}</span>
            <span class="ml-2">ROI</span>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-top">
          <div class="metric-icon">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 7c0 1.66 3.58 3 8 3s8-1.34 8-3-3.58-3-8-3-8 1.34-8 3zm0 0v5c0 1.66 3.58 3 8 3s8-1.34 8-3V7M4 12v5c0 1.66 3.58 3 8 3s8-1.34 8-3v-5" />
            </svg>
          </div>
          <span>Open XRP Position</span>
        </div>
        <div>
          <div class="metric-value">{{ xrpBalance }} <span class="text-lg text-slate-300">XRP</span></div>
          <div class="metric-sub">approx {{ xrpValue }}</div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-top">
          <div class="metric-icon">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h11m0 0l-4-4m4 4l-4 4M17 17H6m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>
          <span>Total Trades</span>
        </div>
        <div>
          <div class="metric-value">{{ totalTrades }}</div>
          <div class="metric-sub">{{ m?.buy_count ?? 0 }} buy / {{ m?.sell_count ?? 0 }} sell</div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-top">
          <div class="metric-icon">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 21h8M12 17v4M7 4h10v5a5 5 0 01-10 0V4zm10 2h3a3 3 0 01-3 3M7 6H4a3 3 0 003 3" />
            </svg>
          </div>
          <span>Win Rate</span>
        </div>
        <div>
          <div class="metric-value" :class="winRateGood ? 'text-emerald-400' : 'text-rose-400'">{{ winRate }}</div>
          <div class="metric-sub">Closed trades</div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-top">
          <div class="metric-icon">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9 9 0 100-18 9 9 0 000 18zm0-13v4l3 2" />
            </svg>
          </div>
          <span>Average Entry</span>
        </div>
        <div>
          <div class="metric-value">{{ averageEntry }}</div>
          <div class="metric-sub">Per XRP</div>
        </div>
      </div>
    </div>

    <div class="panel p-5">
      <div class="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="section-title">{{ currentPair }}</h2>
          <p class="section-subtitle mt-1">{{ priceStore.current ? 'Live price feed' : 'Waiting for live price feed' }}</p>
        </div>
        <div class="segmented">
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
    </div>

    <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <div class="panel p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="section-title">Recent Trades</h2>
          <RouterLink to="/trades" class="text-sm font-medium text-blue-400 hover:text-blue-300">View all</RouterLink>
        </div>
        <div v-if="tradesStore.items.length === 0" class="rounded-xl border border-slate-700/40 bg-slate-950/25 py-10 text-center text-sm text-slate-500">
          No trades yet
        </div>
        <div v-else class="space-y-3">
          <TradeRow v-for="trade in tradesStore.items.slice(0, 4)" :key="trade.id" :trade="trade" />
        </div>
      </div>

      <div class="panel p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="section-title">AI Decisions</h2>
          <RouterLink to="/ai" class="text-sm font-medium text-blue-400 hover:text-blue-300">View all</RouterLink>
        </div>
        <div v-if="aiStore.items.length === 0" class="rounded-xl border border-slate-700/40 bg-slate-950/25 py-10 text-center text-sm text-slate-500">
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
      </div>
    </div>

    <div class="panel flex flex-col gap-3 p-4 text-sm text-slate-400 md:flex-row md:items-center md:justify-between">
      <div>
        <span class="font-semibold text-slate-200">{{ quoteCurrency }} cash balance:</span>
        <span class="ml-2 tabular-nums">{{ quoteBalance }}</span>
      </div>
      <div>
        <span class="font-semibold text-slate-200">Current XRP price:</span>
        <span class="ml-2 tabular-nums">{{ priceStore.current ? formatQuote(priceStore.current.price, 6) : '-' }}</span>
      </div>
    </div>
  </div>
</template>
