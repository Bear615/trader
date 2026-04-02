<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { usePriceStore } from '@/stores/price'
import { usePortfolioStore } from '@/stores/portfolio'
import { useTradesStore } from '@/stores/trades'
import { useAIStore } from '@/stores/ai'
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

const portfolioValue = computed(() => {
  const v = p.value?.total_value_usd ?? p.value?.usd_balance ?? 0
  return v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
})

const roiPct = computed(() => m.value?.roi_pct ?? null)
const roiPositive = computed(() => (roiPct.value ?? 0) >= 0)
const roiLabel = computed(() =>
  roiPct.value !== null ? (roiPositive.value ? '+' : '') + roiPct.value.toFixed(2) + '%' : '—'
)
const winRateGood = computed(() => (m.value?.win_rate_pct ?? 0) >= 50)
</script>

<template>
  <div class="space-y-5 max-w-[1400px]">

    <!-- Header -->
    <div>
      <h1 class="text-lg font-semibold text-gray-100">Dashboard</h1>
      <p class="text-xs text-gray-500 mt-0.5">XRP paper trading overview</p>
    </div>

    <!-- Portfolio hero + stat row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">

      <!-- Portfolio value hero -->
      <div class="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 flex flex-col gap-4">
        <div class="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Portfolio Value</div>
        <div>
          <div class="text-3xl font-bold font-mono tabular-nums text-gray-100 leading-none">${{ portfolioValue }}</div>
          <div class="mt-2">
            <span
              :class="[
                'inline-block text-xs font-semibold font-mono tabular-nums px-2 py-0.5 rounded border',
                roiPositive
                  ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                  : 'text-rose-400 bg-rose-500/10 border-rose-500/20'
              ]"
            >{{ roiLabel }}</span>
            <span class="text-xs text-gray-600 ml-2">all-time return</span>
          </div>
        </div>
        <div class="pt-3 border-t border-white/[0.06] grid grid-cols-2 gap-4">
          <div>
            <div class="text-[10px] text-gray-600 uppercase tracking-wider mb-1">USD</div>
            <div class="text-sm font-mono font-medium text-gray-300 tabular-nums">
              ${{ (p?.usd_balance ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
            </div>
          </div>
          <div>
            <div class="text-[10px] text-gray-600 uppercase tracking-wider mb-1">XRP</div>
            <div class="text-sm font-mono font-medium text-gray-300 tabular-nums">
              {{ p?.xrp_balance?.toFixed(4) ?? '—' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Secondary metrics -->
      <div class="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-4">

        <div class="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 flex flex-col justify-between gap-2">
          <div class="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Trades</div>
          <div class="text-2xl font-bold font-mono tabular-nums text-gray-100">{{ m?.total_trades ?? '—' }}</div>
          <div class="text-[11px] text-gray-600">{{ m?.buy_count ?? 0 }} buy · {{ m?.sell_count ?? 0 }} sell</div>
        </div>

        <div class="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 flex flex-col justify-between gap-2">
          <div class="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Win Rate</div>
          <div
            :class="['text-2xl font-bold font-mono tabular-nums', winRateGood ? 'text-emerald-400' : 'text-rose-400']"
          >{{ m?.win_rate_pct != null ? m.win_rate_pct.toFixed(1) + '%' : '—' }}</div>
          <div class="text-[11px] text-gray-600">of closed trades</div>
        </div>

        <div class="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 flex flex-col justify-between gap-2">
          <div class="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Fees Paid</div>
          <div class="text-2xl font-bold font-mono tabular-nums text-gray-100">
            {{ m?.total_fees_usd != null ? '$' + m.total_fees_usd.toFixed(2) : '—' }}
          </div>
          <div class="text-[11px] text-gray-600">total USD</div>
        </div>

        <div class="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 flex flex-col justify-between gap-2">
          <div class="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Avg Buy</div>
          <div class="text-2xl font-bold font-mono tabular-nums text-gray-100">
            {{ m?.avg_buy_price ? '$' + m.avg_buy_price.toFixed(4) : '—' }}
          </div>
          <div class="text-[11px] text-gray-600">per XRP</div>
        </div>

      </div>
    </div>

    <!-- Price Chart -->
    <div class="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-sm font-semibold text-gray-200">XRP / USD</h2>
          <p class="text-xs text-gray-500 mt-0.5">DIA Oracle · real-time</p>
        </div>
        <div class="flex gap-1">
          <button
            v-for="tf in timeframes"
            :key="tf"
            @click="timeframe = tf"
            :class="[
              'px-2.5 py-1 text-xs rounded-md font-medium transition-colors',
              timeframe === tf
                ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                : 'text-gray-500 hover:text-gray-300 border border-transparent'
            ]"
          >{{ tf }}</button>
        </div>
      </div>
      <PriceChart :data="priceStore.history" :loading="priceStore.loading" />
    </div>

    <!-- Recent trades + AI decisions -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">

      <div class="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-gray-200">Recent Trades</h2>
          <RouterLink to="/trades" class="text-xs text-sky-400 hover:text-sky-300 transition-colors">View all →</RouterLink>
        </div>
        <div v-if="tradesStore.items.length === 0" class="text-sm text-gray-600 text-center py-8">No trades yet</div>
        <div v-else class="space-y-2">
          <TradeRow v-for="trade in tradesStore.items.slice(0, 8)" :key="trade.id" :trade="trade" />
        </div>
      </div>

      <div class="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-gray-200">AI Decisions</h2>
          <RouterLink to="/ai" class="text-xs text-sky-400 hover:text-sky-300 transition-colors">View all →</RouterLink>
        </div>
        <div v-if="aiStore.items.length === 0" class="text-sm text-gray-600 text-center py-8">No AI decisions yet</div>
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
