<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAIStore } from '@/stores/ai'
import type { AIDecision } from '@/api/types'
import { formatDate, formatNumber } from '@/utils/format'

const aiStore = useAIStore()

const selected = ref<AIDecision | null>(null)
const tab = ref<'input' | 'output' | 'info'>('input')
const showRawResponse = ref(false)

onMounted(async () => {
  await aiStore.fetchDecisions(1)
  aiStore.connectWebSocket()
  if (aiStore.items.length) selected.value = aiStore.items[0]
})

watch(() => aiStore.items, (items) => {
  if (!selected.value && items.length) selected.value = items[0]
})

function selectDecision(d: AIDecision) {
  selected.value = d
  tab.value = 'input'
  showRawResponse.value = false
}

function actionClass(action: string) {
  if (action === 'BUY') return 'border-emerald-400/25 bg-emerald-500/10 text-emerald-300'
  if (action === 'SELL') return 'border-rose-400/25 bg-rose-500/10 text-rose-300'
  return 'border-slate-500/30 bg-slate-500/10 text-slate-300'
}

function executionClass(decision: AIDecision) {
  if (decision.executed) return 'border-emerald-400/25 bg-emerald-500/10 text-emerald-300'
  if (decision.execution_error) return 'border-rose-400/25 bg-rose-500/10 text-rose-300'
  return 'border-slate-500/30 bg-slate-500/10 text-slate-400'
}

function executionLabel(decision: AIDecision) {
  if (decision.executed) return 'Executed'
  if (decision.execution_error) return 'Error'
  return 'Skipped'
}

const confidencePct = computed(() =>
  selected.value ? Math.round((selected.value.confidence ?? 0) * 100) : 0,
)

const totalTokens = computed(() =>
  (selected.value?.prompt_tokens ?? 0) + (selected.value?.completion_tokens ?? 0),
)
</script>

<template>
  <div class="view-shell">
    <div class="mobile-screen-header">
      <div>
        <p class="view-kicker">Inspector</p>
        <h1 class="view-title">AI Monitor</h1>
        <p class="view-subtitle">Prompt, response, and execution telemetry adapted for mobile review.</p>
      </div>
      <span class="app-chip border-emerald-400/25 text-emerald-300">
        <span class="status-dot bg-emerald-400" />
        Live
      </span>
    </div>

    <div class="grid grid-cols-1 gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
      <section class="panel max-h-[360px] overflow-hidden p-0 lg:max-h-[calc(100vh-13rem)]">
        <div class="flex items-center justify-between border-b border-slate-800/80 px-4 py-3">
          <h2 class="section-title">Live Feed</h2>
          <span class="text-xs text-slate-500">{{ aiStore.total }} decisions</span>
        </div>
        <div v-if="aiStore.loading && !aiStore.items.length" class="flex h-48 items-center justify-center text-sm text-slate-500">
          Loading
        </div>
        <div v-else-if="!aiStore.items.length" class="flex h-48 items-center justify-center px-4 text-center text-sm text-slate-500">
          No decisions yet. Trigger one from AI Decisions.
        </div>
        <div v-else class="max-h-[304px] overflow-y-auto lg:max-h-[calc(100vh-17rem)]">
          <button
            v-for="d in aiStore.items"
            :key="d.id"
            class="w-full border-b border-slate-800/75 px-4 py-3 text-left transition hover:bg-slate-900/50"
            :class="selected?.id === d.id ? 'bg-blue-500/10' : ''"
            @click="selectDecision(d)"
          >
            <div class="flex items-center gap-2">
              <span class="badge" :class="actionClass(d.action)">{{ d.action }}</span>
              <span class="ml-auto font-mono text-xs tabular-nums text-slate-500">{{ Math.round((d.confidence ?? 0) * 100) }}%</span>
            </div>
            <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
              <div
                class="h-full rounded-full"
                :class="d.action === 'BUY' ? 'bg-emerald-400' : d.action === 'SELL' ? 'bg-rose-400' : 'bg-blue-400'"
                :style="{ width: Math.round((d.confidence ?? 0) * 100) + '%' }"
              />
            </div>
            <div class="mt-2 flex items-center justify-between gap-3 text-[11px] text-slate-500">
              <span class="truncate">{{ d.model_used ?? 'unknown model' }}</span>
              <span class="shrink-0">{{ formatDate(d.timestamp) }}</span>
            </div>
          </button>
        </div>
      </section>

      <section v-if="selected" class="panel overflow-hidden p-0">
        <div class="border-b border-slate-800/80 p-4">
          <div class="flex flex-wrap items-center gap-2">
            <span class="badge" :class="actionClass(selected.action)">{{ selected.action }}</span>
            <span class="badge" :class="executionClass(selected)">{{ executionLabel(selected) }}</span>
            <span class="font-mono text-sm text-slate-300">Decision #{{ selected.id }}</span>
            <span class="ml-auto text-xs text-slate-500">{{ formatDate(selected.timestamp) }}</span>
          </div>

          <div class="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            <div class="card-sm">
              <div class="stat-label">Confidence</div>
              <div class="mt-1 font-mono text-xl font-bold tabular-nums text-blue-300">{{ confidencePct }}%</div>
            </div>
            <div class="card-sm">
              <div class="stat-label">Amount</div>
              <div class="mt-1 font-mono text-xl font-bold tabular-nums text-slate-50">
                {{ selected.xrp_amount != null ? formatNumber(selected.xrp_amount, 4) : '-' }}
              </div>
            </div>
            <div class="card-sm">
              <div class="stat-label">Tokens</div>
              <div class="mt-1 font-mono text-xl font-bold tabular-nums text-slate-50">{{ totalTokens.toLocaleString() }}</div>
            </div>
            <div class="card-sm">
              <div class="stat-label">Model</div>
              <div class="mt-1 truncate font-mono text-sm font-semibold text-slate-200">{{ selected.model_used ?? 'unknown' }}</div>
            </div>
          </div>
        </div>

        <div class="border-b border-slate-800/80 px-4 pt-3">
          <div class="segmented">
            <button
              v-for="t in (['input', 'output', 'info'] as const)"
              :key="t"
              class="segmented-button"
              :class="{ 'segmented-button-active': tab === t }"
              @click="tab = t"
            >
              {{ t === 'input' ? 'Prompt' : t === 'output' ? 'Response' : 'Info' }}
            </button>
          </div>
        </div>

        <div class="p-4">
          <div v-if="tab === 'input'">
            <pre v-if="selected.raw_prompt" class="max-h-[420px] overflow-auto whitespace-pre-wrap rounded-lg border border-slate-800 bg-slate-950/55 p-4 font-mono text-xs leading-relaxed text-slate-300">{{ selected.raw_prompt }}</pre>
            <div v-else class="py-10 text-center text-sm text-slate-500">No prompt recorded for this decision.</div>
          </div>

          <div v-else-if="tab === 'output'" class="space-y-4">
            <div v-if="selected.reasoning" class="mobile-list-card">
              <div class="stat-label">Reasoning</div>
              <p class="mt-2 text-sm leading-relaxed text-slate-300">{{ selected.reasoning }}</p>
            </div>

            <button
              class="text-xs font-semibold text-blue-400 hover:text-blue-300"
              @click="showRawResponse = !showRawResponse"
            >
              {{ showRawResponse ? 'Hide' : 'Show' }} raw response
            </button>
            <pre v-if="showRawResponse && selected.raw_response" class="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-800 bg-slate-950/55 p-4 font-mono text-xs leading-relaxed text-slate-400">{{ selected.raw_response }}</pre>
          </div>

          <dl v-else class="space-y-0">
            <div class="mobile-detail-row">
              <dt class="mobile-detail-label">Decision ID</dt>
              <dd class="mobile-detail-value">#{{ selected.id }}</dd>
            </div>
            <div class="mobile-detail-row">
              <dt class="mobile-detail-label">Prompt tokens</dt>
              <dd class="mobile-detail-value">{{ selected.prompt_tokens ?? '-' }}</dd>
            </div>
            <div class="mobile-detail-row">
              <dt class="mobile-detail-label">Completion tokens</dt>
              <dd class="mobile-detail-value">{{ selected.completion_tokens ?? '-' }}</dd>
            </div>
            <div class="mobile-detail-row">
              <dt class="mobile-detail-label">Execution error</dt>
              <dd class="mobile-detail-value" :class="selected.execution_error ? 'text-rose-400' : ''">
                {{ selected.execution_error ?? '-' }}
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section v-else class="panel flex min-h-[360px] items-center justify-center text-sm text-slate-500">
        Select a decision to inspect
      </section>
    </div>
  </div>
</template>
