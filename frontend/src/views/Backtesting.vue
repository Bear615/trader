<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useBacktestStore } from '@/stores/backtest'
import { useSettingsStore } from '@/stores/settings'
import { currencyCode, formatCurrency, formatDate, formatNumber, formatPercent } from '@/utils/format'
import type { BacktestRun } from '@/api/types'

const store = useBacktestStore()
const settingsStore = useSettingsStore()

const running = ref(false)
const activeResult = ref<BacktestRun | null>(null)
const error = ref('')

const form = ref({
  start_date: '',
  end_date: '',
  initial_capital: 10000,
  maker_fee_pct: 0.1,
  taker_fee_pct: 0.1,
  decisions_per_hour: 12,
  ai_price_window: 50,
  ai_model: 'random',
})

const strategyMode = ref<'random' | 'ai'>('random')
const customModel = ref('gpt-4o')
const quoteCurrency = computed(() => currencyCode(settingsStore.settings['quote_currency']))

const equityPoints = computed(() => {
  const curve = activeResult.value?.result?.equity_curve ?? []
  return curve
    .map((p) => ({ time: new Date(p.timestamp).getTime(), value: Number(p.value) }))
    .filter((p) => Number.isFinite(p.time) && Number.isFinite(p.value))
    .sort((a, b) => a.time - b.time)
})

const equityBounds = computed(() => {
  const values = equityPoints.value.map((p) => p.value)
  if (!values.length) return undefined

  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min
  const fallbackPadding = Math.max(Math.abs(max) * 0.015, 1)
  const padding = range > 0 ? Math.max(range * 0.16, fallbackPadding) : fallbackPadding

  return {
    min: Math.max(0, min - padding),
    max: max + padding,
  }
})

const equityTimeBounds = computed(() => {
  const points = equityPoints.value
  if (!points.length) return undefined
  if (points.length === 1) {
    const padding = 60 * 60 * 1000
    return {
      min: points[0].time - padding,
      max: points[0].time + padding,
    }
  }
  return {
    min: points[0].time,
    max: points[points.length - 1].time,
  }
})

onMounted(async () => {
  const now = new Date()
  const from = new Date(now)
  from.setDate(now.getDate() - 30)
  form.value.end_date = now.toISOString().slice(0, 16)
  form.value.start_date = from.toISOString().slice(0, 16)
  await store.fetchRuns()
  activeResult.value = store.runs.find((run) => run.status === 'done' && run.result) ?? null
})

async function runBacktest() {
  error.value = ''
  running.value = true
  try {
    const run = await store.startBacktest({
      ...form.value,
      start_date: new Date(form.value.start_date).toISOString(),
      end_date: new Date(form.value.end_date).toISOString(),
    })
    if (run.status === 'error') {
      error.value = run.error_message || 'Backtest failed'
    } else {
      activeResult.value = run
    }
  } catch (e: unknown) {
    error.value = (e as Error).message || 'Unexpected error'
  } finally {
    running.value = false
  }
}

const equityChartOptions = computed(() => ({
  chart: { type: 'area', background: 'transparent', toolbar: { show: false }, animations: { enabled: false } },
  stroke: { curve: 'smooth', width: 2, colors: ['#38bdf8'] },
  fill: {
    type: 'gradient',
    gradient: {
      opacityFrom: 0.22,
      opacityTo: 0,
      colorStops: [{ offset: 0, color: '#38bdf8', opacity: 0.22 }, { offset: 100, color: '#38bdf8', opacity: 0 }],
    },
  },
  xaxis: {
    type: 'datetime',
    min: equityTimeBounds.value?.min,
    max: equityTimeBounds.value?.max,
    labels: { style: { colors: '#8b98a8', fontSize: '11px' }, datetimeUTC: false },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    min: equityBounds.value?.min,
    max: equityBounds.value?.max,
    tickAmount: 4,
    forceNiceScale: false,
    labels: { style: { colors: '#8b98a8', fontSize: '11px' }, formatter: (v: number) => formatCurrency(v, quoteCurrency.value, 0) },
  },
  grid: { borderColor: 'rgba(148,163,184,0.12)', strokeDashArray: 4 },
  tooltip: { x: { format: 'dd MMM HH:mm' }, y: { formatter: (v: number) => formatCurrency(v, quoteCurrency.value, 2) } },
  dataLabels: { enabled: false },
}))

const equitySeries = computed(() => {
  return [{ name: 'Portfolio Value', data: equityPoints.value.map((p) => [p.time, p.value]) }]
})

function statusBadge(s: string) {
  if (s === 'done') return 'badge border-emerald-500/25 bg-emerald-500/10 text-emerald-300'
  if (s === 'error') return 'badge border-rose-500/25 bg-rose-500/10 text-rose-300'
  if (s === 'running') return 'badge border-amber-500/25 bg-amber-500/10 text-amber-300'
  return 'badge border-slate-500/30 bg-slate-500/10 text-slate-300'
}

function selectRun(run: BacktestRun) {
  if (run.status === 'done') activeResult.value = run
}
</script>

<template>
  <div class="view-shell">
    <div class="mobile-screen-header">
      <div>
        <p class="view-kicker">Strategy lab</p>
        <h1 class="view-title">Backtest</h1>
        <p class="view-subtitle">Configure, run, and compare historical XRP/{{ quoteCurrency }} strategy results.</p>
      </div>
      <span class="app-chip app-chip-active">{{ quoteCurrency }}</span>
    </div>

    <div class="grid grid-cols-1 gap-5 lg:grid-cols-[380px_minmax(0,1fr)]">
      <section class="panel space-y-4 p-4 md:p-5">
        <div class="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <h2 class="section-title">Setup</h2>
          <span class="app-chip">{{ strategyMode === 'random' ? 'Fast test' : 'AI model' }}</span>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Start</label>
            <input v-model="form.start_date" type="datetime-local" class="input" />
          </div>
          <div>
            <label class="label">End</label>
            <input v-model="form.end_date" type="datetime-local" class="input" />
          </div>
        </div>

        <div>
          <label class="label">Initial Capital ({{ quoteCurrency }})</label>
          <input v-model.number="form.initial_capital" type="number" min="100" class="input" />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Maker Fee %</label>
            <input v-model.number="form.maker_fee_pct" type="number" step="0.01" min="0" class="input" />
          </div>
          <div>
            <label class="label">Taker Fee %</label>
            <input v-model.number="form.taker_fee_pct" type="number" step="0.01" min="0" class="input" />
          </div>
        </div>

        <div>
          <label class="label">Strategy</label>
          <select
            v-model="strategyMode"
            class="select"
            @change="strategyMode === 'random' ? form.ai_model = 'random' : (form.ai_model = customModel)"
          >
            <option value="random">Random engine test</option>
            <option value="ai">AI model</option>
          </select>
        </div>

        <div v-if="strategyMode === 'ai'">
          <label class="label">Model Name</label>
          <input
            v-model="customModel"
            @input="form.ai_model = customModel"
            list="model-suggestions"
            type="text"
            class="input"
            placeholder="gpt-4o"
          />
          <datalist id="model-suggestions">
            <option value="gpt-4o" />
            <option value="gpt-4o-mini" />
            <option value="gpt-4.1" />
            <option value="gpt-4.1-mini" />
            <option value="llama-3.3-70b-versatile" />
            <option value="deepseek-r1-distill-llama-70b" />
          </datalist>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Decisions / Hour</label>
            <input v-model.number="form.decisions_per_hour" type="number" min="1" max="60" class="input" />
          </div>
          <div>
            <label class="label">Price Window</label>
            <input v-model.number="form.ai_price_window" type="number" min="5" max="500" class="input" />
          </div>
        </div>

        <div v-if="error" class="rounded-lg border border-rose-500/25 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
          {{ error }}
        </div>

        <button @click="runBacktest" :disabled="running" class="btn btn-primary w-full">
          <div v-if="running" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          <span>{{ running ? 'Running' : 'Run Backtest' }}</span>
        </button>
      </section>

      <section class="space-y-5">
        <div v-if="activeResult?.result" class="mobile-kpi-grid">
          <div class="card-sm">
            <div class="stat-label">Return</div>
            <div :class="['mt-1 font-mono text-2xl font-bold tabular-nums', activeResult.result.total_return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400']">
              {{ formatPercent(activeResult.result.total_return_pct, 2, true) }}
            </div>
          </div>
          <div class="card-sm">
            <div class="stat-label">Sharpe</div>
            <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-blue-300">{{ activeResult.result.sharpe_ratio.toFixed(3) }}</div>
          </div>
          <div class="card-sm">
            <div class="stat-label">Drawdown</div>
            <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-rose-400">-{{ activeResult.result.max_drawdown_pct.toFixed(2) }}%</div>
          </div>
          <div class="card-sm">
            <div class="stat-label">Trades</div>
            <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-slate-50">{{ activeResult.result.total_trades }}</div>
          </div>
        </div>

        <div v-if="activeResult?.result?.equity_curve?.length" class="panel p-4 md:p-5">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="section-title">Equity Curve</h3>
            <span class="app-chip app-chip-active">{{ formatCurrency(activeResult.result.final_value, quoteCurrency, 2) }}</span>
          </div>
          <apexchart type="area" height="260" :options="equityChartOptions" :series="equitySeries" />
        </div>

        <div v-else-if="!running" class="panel py-16 text-center">
          <p class="text-sm text-slate-500">Configure a backtest and run it to see results here.</p>
          <p class="mt-1 text-xs text-slate-600">Seed price history from Admin first when the chart is empty.</p>
        </div>

        <div v-if="running" class="panel py-16 text-center">
          <div class="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
          <p class="text-sm text-slate-400">Backtest running</p>
          <p class="mt-1 text-xs text-slate-600">AI mode may take a few minutes depending on date range.</p>
        </div>

        <section v-if="store.runs.length > 0" class="panel p-4 md:p-5">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="section-title">Run History</h2>
            <span class="text-xs text-slate-500">{{ store.runs.length }} runs</span>
          </div>

          <div class="space-y-3">
            <button
              v-for="run in store.runs"
              :key="run.id"
              class="mobile-list-card w-full text-left"
              :class="activeResult?.id === run.id ? 'border-blue-400/35 bg-blue-500/10' : ''"
              @click="selectRun(run)"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <span :class="statusBadge(run.status)">{{ run.status }}</span>
                    <span class="badge-ai">{{ run.ai_model }}</span>
                  </div>
                  <div class="mt-2 text-sm font-semibold text-slate-100">
                    {{ formatDate(run.start_date) }} to {{ formatDate(run.end_date) }}
                  </div>
                  <div class="mt-1 text-xs text-slate-500">{{ formatCurrency(run.initial_capital, quoteCurrency, 0) }} capital</div>
                </div>
                <div class="text-right">
                  <div
                    class="font-mono text-sm font-bold tabular-nums"
                    :class="(run.result?.total_return_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'"
                  >
                    {{ run.result ? formatPercent(run.result.total_return_pct, 2, true) : '-' }}
                  </div>
                  <div class="mt-1 text-xs text-slate-500">{{ run.result ? formatNumber(run.result.total_trades, 0) + ' trades' : 'No result' }}</div>
                </div>
              </div>
            </button>
          </div>
        </section>
      </section>
    </div>
  </div>
</template>
