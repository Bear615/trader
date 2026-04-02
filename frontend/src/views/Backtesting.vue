<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useBacktestStore } from '@/stores/backtest'
import type { BacktestRun } from '@/api/types'

const store = useBacktestStore()

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

// Separate strategy mode from the freeform model name so the form stays clean
const strategyMode = ref<'random' | 'ai'>('random')
const customModel = ref('gpt-4o')

onMounted(async () => {
  const now = new Date()
  const from = new Date(now)
  from.setDate(now.getDate() - 30)
  form.value.end_date = now.toISOString().slice(0, 16)
  form.value.start_date = from.toISOString().slice(0, 16)
  await store.fetchRuns()
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
  stroke: { curve: 'smooth', width: 2, colors: ['#10b981'] },
  fill: {
    type: 'gradient',
    gradient: {
      opacityFrom: 0.25, opacityTo: 0.0,
      colorStops: [{ offset: 0, color: '#10b981', opacity: 0.25 }, { offset: 100, color: '#10b981', opacity: 0 }],
    },
  },
  xaxis: {
    type: 'datetime',
    labels: { style: { colors: '#6b7280', fontSize: '11px' }, datetimeUTC: false },
    axisBorder: { show: false }, axisTicks: { show: false },
  },
  yaxis: { labels: { style: { colors: '#6b7280', fontSize: '11px' }, formatter: (v: number) => '$' + v.toFixed(0) } },
  grid: { borderColor: '#21262d', strokeDashArray: 4 },
  tooltip: { x: { format: 'dd MMM HH:mm' }, y: { formatter: (v: number) => '$' + v.toFixed(2) } },
  dataLabels: { enabled: false },
}))

const equitySeries = computed(() => {
  const curve = activeResult.value?.result?.equity_curve ?? []
  return [{ name: 'Portfolio Value', data: curve.map((p) => [new Date(p.timestamp).getTime(), p.value]) }]
})

function statusBadge(s: string) {
  if (s === 'done') return 'badge text-emerald-400 bg-emerald-500/10 border-emerald-500/25'
  if (s === 'error') return 'badge text-rose-400 bg-rose-500/10 border-rose-500/25'
  if (s === 'running') return 'badge text-amber-400 bg-amber-500/10 border-amber-500/25'
  return 'badge text-gray-400 bg-gray-500/10 border-gray-500/25'
}

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div class="space-y-6 max-w-[1200px]">
    <!-- Header -->
    <div>
      <h1 class="text-xl font-semibold text-gray-100">Backtesting</h1>
      <p class="text-sm text-gray-500 mt-0.5">Replay historical XRP price data through AI trading strategies</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Config form -->
      <div class="card lg:col-span-1 space-y-4">
        <h2 class="text-sm font-semibold text-gray-200 pb-3 border-b border-surface-700">Configuration</h2>

        <div>
          <label class="label">Start Date</label>
          <input v-model="form.start_date" type="datetime-local" class="input" />
        </div>
        <div>
          <label class="label">End Date</label>
          <input v-model="form.end_date" type="datetime-local" class="input" />
        </div>
        <div>
          <label class="label">Initial Capital (USD)</label>
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
          <label class="label">Decisions Per Hour</label>
          <input v-model.number="form.decisions_per_hour" type="number" min="1" max="60" class="input" />
          <p class="text-[11px] text-gray-600 mt-1">Lower = fewer AI calls = cheaper &amp; faster</p>
        </div>
        <div>
          <label class="label">AI Price Window</label>
          <input v-model.number="form.ai_price_window" type="number" min="5" max="500" class="input" />
          <p class="text-[11px] text-gray-600 mt-1">Number of recent price points fed to AI</p>
        </div>
        <div>
          <label class="label">AI Strategy</label>
          <select
            v-model="strategyMode"
            class="select"
            @change="strategyMode === 'random' ? form.ai_model = 'random' : (form.ai_model = customModel)"
          >
            <option value="random">Random (free — engine test)</option>
            <option value="ai">AI Model</option>
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
            placeholder="e.g. gpt-4o, llama3.2, mixtral-8x7b-32768"
          />
          <datalist id="model-suggestions">
            <option value="gpt-4o" />
            <option value="gpt-4o-mini" />
            <option value="gpt-4.1" />
            <option value="gpt-4.1-mini" />
            <option value="o3-mini" />
            <option value="llama-3.3-70b-versatile" />
            <option value="deepseek-r1-distill-llama-70b" />
            <option value="llama3.2" />
            <option value="mistral" />
            <option value="gemma2" />
            <option value="phi3" />
          </datalist>
          <p class="text-[11px] text-gray-600 mt-1">Uses the provider &amp; API key configured in Admin settings</p>
        </div>

        <div v-if="error" class="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/25 rounded-lg px-3 py-2">
          {{ error }}
        </div>

        <button @click="runBacktest" :disabled="running" class="btn btn-primary w-full">
          <div v-if="running" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          <span>{{ running ? 'Running…' : 'Run Backtest' }}</span>
        </button>
      </div>

      <!-- Results panel -->
      <div class="lg:col-span-2 space-y-5">
        <!-- Metric cards -->
        <div v-if="activeResult?.result" class="grid grid-cols-3 gap-3">
          <div class="card-sm text-center">
            <div class="stat-label">Total Return</div>
            <div :class="['text-xl font-bold font-mono mt-1.5 tabular-nums', activeResult.result.total_return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400']">
              {{ activeResult.result.total_return_pct >= 0 ? '+' : '' }}{{ activeResult.result.total_return_pct.toFixed(2) }}%
            </div>
          </div>
          <div class="card-sm text-center">
            <div class="stat-label">Sharpe Ratio</div>
            <div class="text-xl font-bold font-mono text-sky-400 mt-1.5 tabular-nums">{{ activeResult.result.sharpe_ratio.toFixed(3) }}</div>
          </div>
          <div class="card-sm text-center">
            <div class="stat-label">Max Drawdown</div>
            <div class="text-xl font-bold font-mono text-rose-400 mt-1.5 tabular-nums">-{{ activeResult.result.max_drawdown_pct.toFixed(2) }}%</div>
          </div>
          <div class="card-sm text-center">
            <div class="stat-label">Win Rate</div>
            <div class="text-xl font-bold font-mono text-gray-100 mt-1.5 tabular-nums">{{ activeResult.result.win_rate_pct.toFixed(1) }}%</div>
          </div>
          <div class="card-sm text-center">
            <div class="stat-label">Total Trades</div>
            <div class="text-xl font-bold font-mono text-gray-100 mt-1.5 tabular-nums">{{ activeResult.result.total_trades }}</div>
          </div>
          <div class="card-sm text-center">
            <div class="stat-label">Final Value</div>
            <div class="text-xl font-bold font-mono text-gray-100 mt-1.5 tabular-nums">${{ activeResult.result.final_value.toFixed(2) }}</div>
          </div>
        </div>

        <!-- Equity curve -->
        <div v-if="activeResult?.result?.equity_curve?.length" class="card">
          <h3 class="text-sm font-semibold text-gray-200 mb-4">Equity Curve</h3>
          <apexchart type="area" height="260" :options="equityChartOptions" :series="equitySeries" />
        </div>

        <!-- Idle state -->
        <div v-else-if="!running" class="card text-center py-16">
          <p class="text-gray-600 text-sm">Configure a backtest and click Run to see results here.</p>
          <p class="text-gray-700 text-xs mt-1">Tip: seed price history from the Admin panel first.</p>
        </div>

        <!-- Running state -->
        <div v-if="running" class="card text-center py-16">
          <div class="inline-block w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin mb-4" />
          <p class="text-gray-400 text-sm">Backtest running…</p>
          <p class="text-gray-600 text-xs mt-1">AI mode may take a few minutes depending on date range.</p>
        </div>
      </div>
    </div>

    <!-- Past runs table -->
    <div v-if="store.runs.length > 0" class="card">
      <h2 class="text-sm font-semibold text-gray-200 mb-4">Past Runs</h2>
      <div class="table-wrapper">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Date Range</th>
              <th class="text-right">Capital</th>
              <th>Strategy</th>
              <th class="text-right">Return</th>
              <th class="text-right">Sharpe</th>
              <th class="text-right">Max DD</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in store.runs" :key="run.id">
              <td class="text-gray-500 font-mono">#{{ run.id }}</td>
              <td class="text-xs text-gray-400">{{ fmtDate(run.start_date) }} → {{ fmtDate(run.end_date) }}</td>
              <td class="text-right font-mono tabular-nums">${{ run.initial_capital.toFixed(0) }}</td>
              <td><span class="badge-ai">{{ run.ai_model }}</span></td>
              <td
                class="text-right font-mono tabular-nums"
                :class="(run.result?.total_return_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'"
              >
                {{ run.result ? ((run.result.total_return_pct >= 0 ? '+' : '') + run.result.total_return_pct.toFixed(2) + '%') : '—' }}
              </td>
              <td class="text-right font-mono text-gray-400 tabular-nums">{{ run.result?.sharpe_ratio?.toFixed(3) ?? '—' }}</td>
              <td class="text-right font-mono text-rose-400 tabular-nums">{{ run.result?.max_drawdown_pct !== undefined ? '-' + run.result.max_drawdown_pct.toFixed(2) + '%' : '—' }}</td>
              <td><span :class="statusBadge(run.status)">{{ run.status }}</span></td>
              <td>
                <button
                  v-if="run.status === 'done'"
                  @click="activeResult = run"
                  class="text-xs text-sky-400 hover:text-sky-300 transition-colors"
                >View</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

