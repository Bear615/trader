<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useAIStore } from '@/stores/ai'
import AIDecisionCard from '@/components/AIDecisionCard.vue'
import axios from 'axios'

const store = useAIStore()

const totalPages = computed(() => Math.ceil(store.total / store.perPage))
const filterAction = ref<'ALL' | 'BUY' | 'SELL' | 'HOLD'>('ALL')
const filterExecuted = ref(false)
const triggering = ref(false)
const triggerError = ref('')

const buys = computed(() => store.items.filter((d) => d.action === 'BUY').length)
const sells = computed(() => store.items.filter((d) => d.action === 'SELL').length)
const holds = computed(() => store.items.filter((d) => d.action === 'HOLD').length)
const executed = computed(() => store.items.filter((d) => d.executed).length)
const avgConf = computed(() => {
  if (!store.items.length) return 0
  return Math.round(store.items.reduce((a, d) => a + d.confidence, 0) / store.items.length * 100)
})

const filteredItems = computed(() =>
  store.items.filter((d) => {
    if (filterAction.value !== 'ALL' && d.action !== filterAction.value) return false
    if (filterExecuted.value && !d.executed) return false
    return true
  }),
)

onMounted(() => {
  store.fetchDecisions(1)
  store.connectWebSocket()
})

async function trigger() {
  if (triggering.value) return
  triggering.value = true
  triggerError.value = ''
  try {
    const decision = await store.triggerDecision()
    if (decision.action !== 'HOLD' && !decision.executed) {
      triggerError.value = decision.execution_error
        ? `Trade failed: ${decision.execution_error}`
        : 'Trade was not executed. The AI has been asked to retry with a corrected amount.'
    }
    await store.fetchDecisions(1)
  } catch (e: unknown) {
    triggerError.value = axios.isAxiosError(e)
      ? (e.response?.data?.detail ?? e.message)
      : String(e)
  } finally {
    triggering.value = false
  }
}

function distributionWidth(count: number) {
  return store.items.length ? `${count / store.items.length * 100}%` : '0%'
}
</script>

<template>
  <div class="view-shell">
    <div class="mobile-screen-header">
      <div>
        <p class="view-kicker">Decision log</p>
        <h1 class="view-title">AI Decisions</h1>
        <p class="view-subtitle">{{ store.total.toLocaleString() }} decisions logged, with execution state visible.</p>
      </div>
      <button @click="trigger" :disabled="triggering" class="btn btn-primary btn-sm shrink-0">
        <div v-if="triggering" class="h-3.5 w-3.5 animate-spin rounded-full border border-white border-t-transparent" />
        <svg v-else class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        {{ triggering ? 'Thinking' : 'Trigger' }}
      </button>
    </div>

    <div v-if="triggerError" class="rounded-lg border border-rose-500/25 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
      {{ triggerError }}
    </div>

    <section class="mobile-kpi-grid">
      <div class="card-sm">
        <div class="stat-label">Buy</div>
        <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-emerald-400">{{ buys }}</div>
      </div>
      <div class="card-sm">
        <div class="stat-label">Sell</div>
        <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-rose-400">{{ sells }}</div>
      </div>
      <div class="card-sm">
        <div class="stat-label">Hold</div>
        <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-slate-300">{{ holds }}</div>
      </div>
      <div class="card-sm">
        <div class="stat-label">Avg Conf.</div>
        <div class="mt-1 font-mono text-2xl font-bold tabular-nums text-blue-300">{{ avgConf }}%</div>
      </div>
    </section>

    <section v-if="store.items.length" class="panel space-y-3 p-4">
      <div class="flex items-center justify-between text-xs text-slate-500">
        <span>Distribution</span>
        <span>{{ executed }} executed / {{ store.items.length }} visible</span>
      </div>
      <div class="flex h-2 overflow-hidden rounded-full bg-slate-800">
        <div class="bg-emerald-400" :style="{ width: distributionWidth(buys) }" />
        <div class="bg-rose-400" :style="{ width: distributionWidth(sells) }" />
        <div class="bg-slate-500" :style="{ width: distributionWidth(holds) }" />
      </div>
      <div class="flex gap-4 text-[11px] text-slate-500">
        <span>BUY {{ store.items.length ? Math.round(buys / store.items.length * 100) : 0 }}%</span>
        <span>SELL {{ store.items.length ? Math.round(sells / store.items.length * 100) : 0 }}%</span>
        <span>HOLD {{ store.items.length ? Math.round(holds / store.items.length * 100) : 0 }}%</span>
      </div>
    </section>

    <div v-if="store.items.length" class="sticky-mobile-action flex items-center justify-between gap-3">
      <div class="segmented overflow-x-auto">
        <button
          v-for="f in (['ALL', 'BUY', 'SELL', 'HOLD'] as const)"
          :key="f"
          @click="filterAction = f"
          class="segmented-button"
          :class="{ 'segmented-button-active': filterAction === f }"
        >
          {{ f }}
        </button>
      </div>
      <label class="flex shrink-0 items-center gap-2 text-xs text-slate-500">
        <input v-model="filterExecuted" type="checkbox" class="h-3.5 w-3.5 accent-blue-500" />
        Executed
      </label>
    </div>

    <div v-if="store.loading && store.items.length === 0" class="flex justify-center py-20">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
    </div>

    <div v-else-if="store.items.length === 0" class="panel py-16 text-center">
      <p class="text-sm font-medium text-slate-400">No AI decisions yet</p>
      <p class="mt-1 text-xs text-slate-600">Enable AI trading in Admin or trigger a manual decision.</p>
    </div>

    <div v-else-if="filteredItems.length === 0" class="panel py-12 text-center">
      <p class="text-sm text-slate-500">No decisions match the current filter.</p>
      <button @click="filterAction = 'ALL'; filterExecuted = false" class="mt-3 text-xs font-semibold text-blue-400 hover:text-blue-300">
        Clear filters
      </button>
    </div>

    <div v-else class="space-y-2">
      <AIDecisionCard
        v-for="(decision, i) in filteredItems"
        :key="decision.id"
        :decision="decision"
        :index="i"
      />
    </div>

    <div v-if="totalPages > 1" class="flex items-center justify-between pt-1">
      <p class="text-xs text-slate-500">
        Page {{ store.page }} of {{ totalPages }}
      </p>
      <div class="flex gap-2">
        <button
          @click="store.fetchDecisions(store.page - 1)"
          :disabled="store.page === 1"
          class="btn btn-ghost btn-sm"
        >Prev</button>
        <button
          @click="store.fetchDecisions(store.page + 1)"
          :disabled="store.page >= totalPages"
          class="btn btn-ghost btn-sm"
        >Next</button>
      </div>
    </div>
  </div>
</template>
