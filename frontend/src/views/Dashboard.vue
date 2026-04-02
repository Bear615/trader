<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { usePriceStore } from '@/stores/price'
import { usePortfolioStore } from '@/stores/portfolio'
import { useTradesStore } from '@/stores/trades'
import { useAIStore } from '@/stores/ai'
import StatCard from '@/components/StatCard.vue'
import PriceChart from '@/components/PriceChart.vue'
import AIDecisionCard from '@/components/AIDecisionCard.vue'
import TradeRow from '@/components/TradeRow.vue'

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

const roiClass = computed(() =>
  (m.value?.roi_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
)
const winRateClass = computed(() =>
  (m.value?.win_rate_pct ?? 0) >= 50 ? 'text-emerald-400' : 'text-rose-400'
)
</script>

<template>
  <div class="space-y-6 max-w-[1400px]">
    <!-- Page header -->
    <div>
      <h1 class="text-xl font-semibold text-gray-100">Dashboard</h1>
      <p class="text-sm text-gray-500 mt-0.5">Live XRP paper trading overview</p>
    </div>

    <!-- Stats row 1 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Portfolio Value"
        :value="'$' + (p?.total_value_usd ?? p?.usd_balance ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })"
      />
      <StatCard
        label="ROI"
        :value="m?.roi_pct != null ? ((m.roi_pct >= 0 ? '+' : '') + m.roi_pct.toFixed(2) + '%') : '—'"
        :valueClass="roiClass"
      />
      <StatCard
        label="XRP Balance"
        :value="(p?.xrp_balance?.toFixed(4) ?? '—') + ' XRP'"
      />
      <StatCard
        label="USD Balance"
        :value="'$' + (p?.usd_balance ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })"
      />
    </div>

    <!-- Stats row 2 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard label="Total Trades" :value="String(m?.total_trades ?? '—')" />
      <StatCard
        label="Win Rate"
        :value="m?.win_rate_pct != null ? m.win_rate_pct.toFixed(1) + '%' : '—'"
        :valueClass="winRateClass"
      />
      <StatCard label="Total Fees" :value="m?.total_fees_usd != null ? '$' + m.total_fees_usd.toFixed(4) : '—'" />
      <StatCard
        label="Avg Buy Price"
        :value="m?.avg_buy_price ? '$' + m.avg_buy_price.toFixed(6) : '—'"
      />
    </div>

    <!-- Price Chart -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-sm font-semibold text-gray-200">XRP / USD</h2>
          <p class="text-xs text-gray-500 mt-0.5">Polled from DIA Oracle in real time</p>
        </div>
        <div class="flex gap-1">
          <button
            v-for="tf in timeframes"
            :key="tf"
            @click="timeframe = tf"
            :class="[
              'px-2.5 py-1 text-xs rounded-md font-medium transition-all',
              timeframe === tf
                ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.07] border border-transparent'
            ]"
          >{{ tf }}</button>
        </div>
      </div>
      <PriceChart :data="priceStore.history" :loading="priceStore.loading" />
    </div>

    <!-- Recent trades + AI decisions -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Trades -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-gray-200">Recent Trades</h2>
          <RouterLink to="/trades" class="text-xs text-sky-400 hover:text-sky-300 transition-colors">View all →</RouterLink>
        </div>
        <div v-if="tradesStore.items.length === 0" class="text-sm text-gray-600 text-center py-8">
          No trades yet
        </div>
        <div v-else class="space-y-2 animate-list">
          <TradeRow
            v-for="trade in tradesStore.items.slice(0, 8)"
            :key="trade.id"
            :trade="trade"
          />
        </div>
      </div>

      <!-- AI Decisions -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-gray-200">AI Decisions</h2>
          <RouterLink to="/ai" class="text-xs text-sky-400 hover:text-sky-300 transition-colors">View all →</RouterLink>
        </div>
        <div v-if="aiStore.items.length === 0" class="text-sm text-gray-600 text-center py-8">
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
  </div>
</template>
