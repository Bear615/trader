<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useAIStore } from '@/stores/ai'
import AIDecisionCard from '@/components/AIDecisionCard.vue'

const store = useAIStore()

const totalPages    = computed(() => Math.ceil(store.total / store.perPage))
const filterAction  = ref<'ALL' | 'BUY' | 'SELL' | 'HOLD'>('ALL')
const filterExecuted = ref(false)

const buys  = computed(() => store.items.filter(d => d.action === 'BUY').length)
const sells = computed(() => store.items.filter(d => d.action === 'SELL').length)
const holds = computed(() => store.items.filter(d => d.action === 'HOLD').length)
const avgConf = computed(() => {
  if (!store.items.length) return 0
  return Math.round(store.items.reduce((a, d) => a + d.confidence, 0) / store.items.length * 100)
})
const executed = computed(() => store.items.filter(d => d.executed).length)

const filteredItems = computed(() =>
  store.items.filter(d => {
    if (filterAction.value !== 'ALL' && d.action !== filterAction.value) return false
    if (filterExecuted.value && !d.executed) return false
    return true
  })
)

onMounted(() => {
  store.fetchDecisions(1)
  store.connectWebSocket()
})

async function trigger() {
  await store.triggerDecision()
}
</script>

<template>
  <div class="space-y-6 max-w-[960px]">

    <!-- ── Header ── -->
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-xl font-semibold text-gray-100">AI Decisions</h1>
        <p class="text-sm text-gray-500 mt-1">
          {{ store.total.toLocaleString() }} total decisions logged
        </p>
      </div>
      <button @click="trigger" class="btn btn-primary btn-sm shrink-0">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Trigger Now
      </button>
    </div>

    <!-- ── Stats row ── -->
    <div v-if="store.items.length" class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <!-- BUY -->
      <div class="rounded-xl bg-emerald-500/[0.06] border border-emerald-500/20 px-4 py-3 flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-emerald-500/15 flex items-center justify-center shrink-0">
          <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
          </svg>
        </div>
        <div>
          <p class="text-[10px] uppercase tracking-wider text-emerald-700 leading-none">Buy</p>
          <p class="text-xl font-bold tabular-nums text-emerald-400 mt-0.5">{{ buys }}</p>
        </div>
      </div>
      <!-- SELL -->
      <div class="rounded-xl bg-rose-500/[0.06] border border-rose-500/20 px-4 py-3 flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-rose-500/15 flex items-center justify-center shrink-0">
          <svg class="w-4 h-4 text-rose-400" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6L9 12.75l4.306-4.307a11.95 11.95 0 015.814 5.519l2.74 1.22m0 0l-5.94 2.28m5.94-2.28l-2.28-5.941" />
          </svg>
        </div>
        <div>
          <p class="text-[10px] uppercase tracking-wider text-rose-700 leading-none">Sell</p>
          <p class="text-xl font-bold tabular-nums text-rose-400 mt-0.5">{{ sells }}</p>
        </div>
      </div>
      <!-- HOLD -->
      <div class="rounded-xl bg-white/[0.03] border border-white/[0.07] px-4 py-3 flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-white/[0.05] flex items-center justify-center shrink-0">
          <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
          </svg>
        </div>
        <div>
          <p class="text-[10px] uppercase tracking-wider text-gray-600 leading-none">Hold</p>
          <p class="text-xl font-bold tabular-nums text-slate-400 mt-0.5">{{ holds }}</p>
        </div>
      </div>
      <!-- Avg Confidence -->
      <div class="rounded-xl bg-white/[0.03] border border-white/[0.07] px-4 py-3 flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center shrink-0">
          <svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div>
          <p class="text-[10px] uppercase tracking-wider text-gray-600 leading-none">Avg Conf.</p>
          <p class="text-xl font-bold tabular-nums text-sky-400 mt-0.5">{{ avgConf }}%</p>
        </div>
      </div>
    </div>

    <!-- ── Action/ratio bar ── -->
    <div v-if="store.items.length" class="rounded-xl bg-white/[0.025] border border-white/[0.06] px-4 py-3 space-y-2">
      <div class="flex items-center justify-between text-[10px] uppercase tracking-wider text-gray-600">
        <span>Decision distribution — this page</span>
        <span>
          <span class="text-sky-500/70">{{ executed }} executed</span>
          <span class="text-gray-700 mx-1.5">·</span>
          <span class="text-gray-600">{{ store.items.length - executed }} skipped</span>
        </span>
      </div>
      <div class="flex h-1.5 rounded-full overflow-hidden gap-px bg-white/[0.04]">
        <div
          class="bg-emerald-500/70 transition-all duration-700"
          :style="{ width: store.items.length ? (buys / store.items.length * 100) + '%' : '0%' }"
        />
        <div
          class="bg-rose-500/70 transition-all duration-700"
          :style="{ width: store.items.length ? (sells / store.items.length * 100) + '%' : '0%' }"
        />
        <div
          class="bg-slate-600/50 flex-1 transition-all duration-700"
        />
      </div>
      <div class="flex gap-4 text-[10px]">
        <span class="flex items-center gap-1.5 text-gray-500">
          <span class="w-2 h-2 rounded-sm bg-emerald-500/70 inline-block" />
          BUY {{ store.items.length ? Math.round(buys / store.items.length * 100) : 0 }}%
        </span>
        <span class="flex items-center gap-1.5 text-gray-500">
          <span class="w-2 h-2 rounded-sm bg-rose-500/70 inline-block" />
          SELL {{ store.items.length ? Math.round(sells / store.items.length * 100) : 0 }}%
        </span>
        <span class="flex items-center gap-1.5 text-gray-500">
          <span class="w-2 h-2 rounded-sm bg-slate-600/50 inline-block" />
          HOLD {{ store.items.length ? Math.round(holds / store.items.length * 100) : 0 }}%
        </span>
      </div>
    </div>

    <!-- ── Filter bar ── -->
    <div v-if="store.items.length" class="flex items-center justify-between gap-4 flex-wrap">
      <div class="flex items-center gap-1 p-1 bg-white/[0.03] border border-white/[0.06] rounded-xl">
        <button
          v-for="f in (['ALL', 'BUY', 'SELL', 'HOLD'] as const)"
          :key="f"
          @click="filterAction = f"
          class="px-3 py-1.5 text-xs font-semibold rounded-lg transition-all duration-200"
          :class="filterAction === f
            ? f === 'BUY'  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            : f === 'SELL' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
            : f === 'HOLD' ? 'bg-slate-500/20 text-slate-300 border border-slate-600/30'
            :                'bg-white/[0.08] text-gray-200 border border-white/[0.1]'
            : 'text-gray-500 hover:text-gray-300 border border-transparent'"
        >
          {{ f }}
        </button>
      </div>
      <label class="flex items-center gap-2 text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition-colors select-none">
        <input type="checkbox" v-model="filterExecuted" class="w-3.5 h-3.5 accent-sky-500 rounded" />
        Executed only
      </label>
    </div>

    <!-- ── Loading ── -->
    <div v-if="store.loading && store.items.length === 0" class="flex justify-center py-20">
      <div class="w-6 h-6 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- ── Empty state ── -->
    <div
      v-else-if="store.items.length === 0"
      class="rounded-2xl border border-white/[0.07] bg-white/[0.02] text-center py-20"
    >
      <div class="w-12 h-12 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mx-auto mb-4">
        <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1 1 .03 2.798-1.338 2.798H4.136c-1.368 0-2.337-1.798-1.338-2.798L4.2 15.3" />
        </svg>
      </div>
      <p class="text-gray-400 text-sm font-medium">No AI decisions yet</p>
      <p class="text-gray-600 text-xs mt-1.5">Enable AI trading in the Admin panel to start generating decisions.</p>
    </div>

    <!-- ── No filter results ── -->
    <div
      v-else-if="filteredItems.length === 0"
      class="rounded-2xl border border-white/[0.06] text-center py-12"
    >
      <p class="text-gray-500 text-sm">No decisions match the current filter.</p>
      <button @click="filterAction = 'ALL'; filterExecuted = false" class="mt-3 text-xs text-sky-500 hover:text-sky-400 transition-colors">
        Clear filters
      </button>
    </div>

    <!-- ── Decision cards ── -->
    <div v-else class="space-y-2">
      <AIDecisionCard
        v-for="(decision, i) in filteredItems"
        :key="decision.id"
        :decision="decision"
        :index="i"
      />
    </div>

    <!-- ── Pagination ── -->
    <div v-if="totalPages > 1" class="flex items-center justify-between pt-1">
      <p class="text-xs text-gray-600">
        Page {{ store.page }} of {{ totalPages }}
        <span class="text-gray-700 ml-1">· {{ store.total.toLocaleString() }} total</span>
      </p>
      <div class="flex gap-2">
        <button
          @click="store.fetchDecisions(store.page - 1)"
          :disabled="store.page === 1"
          class="btn btn-ghost btn-sm"
        >← Prev</button>
        <button
          @click="store.fetchDecisions(store.page + 1)"
          :disabled="store.page >= totalPages"
          class="btn btn-ghost btn-sm"
        >Next →</button>
      </div>
    </div>

  </div>
</template>
