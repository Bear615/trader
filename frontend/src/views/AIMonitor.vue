<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAIStore } from '@/stores/ai'
import type { AIDecision } from '@/api/types'
import { formatDate } from '@/utils/format'

const aiStore = useAIStore()

const selected = ref<AIDecision | null>(null)
const tab = ref<'input' | 'output' | 'info'>('input')
const showRawResponse = ref(false)

onMounted(async () => {
  await aiStore.fetchDecisions(1)
  aiStore.connectWebSocket()
  if (aiStore.items.length) selected.value = aiStore.items[0]
})

function selectDecision(d: AIDecision) {
  selected.value = d
  tab.value = 'input'
  showRawResponse.value = false
}

function fmt(ts: string) {
  return formatDate(ts)
}

function actionColor(a: string) {
  if (a === 'BUY') return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25'
  if (a === 'SELL') return 'text-rose-400 bg-rose-500/10 border-rose-500/25'
  return 'text-gray-400 border-white/[0.12]' + '; background: rgba(255,255,255,0.07)'
}

const confidencePct = computed(() =>
  selected.value ? Math.round((selected.value.confidence ?? 0) * 100) : 0,
)

const totalTokens = computed(() =>
  (selected.value?.prompt_tokens ?? 0) + (selected.value?.completion_tokens ?? 0),
)
</script>

<template>
  <!-- Full-height split-pane layout (fills the padded main area) -->
  <div class="flex flex-col h-[calc(100vh-7rem)] min-h-[400px]">
    <!-- Page header -->
    <div class="flex items-center gap-4 pb-4 flex-shrink-0">
      <div>
        <h1 class="text-xl font-semibold text-gray-100">AI I/O Monitor</h1>
        <p class="text-xs text-gray-500 mt-0.5">Live feed of every prompt sent to the model and its raw response</p>
      </div>
      <div class="ml-auto flex items-center gap-2 text-xs text-gray-500">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-sky-500"></span>
        </span>
        Live &nbsp;·&nbsp; {{ aiStore.total }} decisions
      </div>
    </div>

    <!-- Split pane -->
    <div class="flex flex-1 min-h-0 rounded-2xl overflow-hidden" style="background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%); border: 1px solid rgba(255,255,255,0.09); backdrop-filter: blur(22px) saturate(160%);">  
      <!-- Left: decision list -->
      <div class="w-72 flex-shrink-0 overflow-y-auto flex flex-col" style="border-right: 1px solid rgba(255,255,255,0.07); background: rgba(0,0,0,0.2);">
        <div
          v-if="aiStore.loading && !aiStore.items.length"
          class="flex-1 flex items-center justify-center text-gray-600 text-sm"
        >Loading…</div>
        <div
          v-else-if="!aiStore.items.length"
          class="flex-1 flex items-center justify-center text-gray-600 text-sm px-4 text-center"
        >
          No decisions yet.<br />Trigger one from the Admin panel.
        </div>
        <button
          v-for="d in aiStore.items"
          :key="d.id"
          class="w-full text-left px-4 py-3 transition-colors flex-shrink-0"
          :class="selected?.id === d.id ? 'border-l-2 border-l-sky-500' : ''"
          :style="selected?.id === d.id ? 'background: rgba(14,165,233,0.10); border-bottom: 1px solid rgba(255,255,255,0.05);' : 'border-bottom: 1px solid rgba(255,255,255,0.05); border-left: 2px solid transparent;'"
          @mouseenter="e => { if (selected?.id !== d.id) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)'; }"
          @mouseleave="e => { if (selected?.id !== d.id) (e.currentTarget as HTMLElement).style.background = ''; }"
          @click="selectDecision(d)"
        >
          <div class="flex items-center gap-2 mb-1.5">
            <span
              class="px-1.5 py-0.5 rounded text-[10px] font-bold border"
              :class="actionColor(d.action)"
            >{{ d.action }}</span>
            <span class="text-[10px] text-gray-500 ml-auto tabular-nums">{{ fmt(d.timestamp) }}</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="flex-1 bg-surface-700 rounded-full h-1 overflow-hidden">
              <div
                class="h-1 rounded-full"
                :class="d.action === 'BUY' ? 'bg-emerald-500' : d.action === 'SELL' ? 'bg-rose-500' : 'bg-sky-500'"
                :style="{ width: Math.round((d.confidence ?? 0) * 100) + '%' }"
              ></div>
            </div>
            <span class="text-[10px] text-gray-500 tabular-nums">{{ Math.round((d.confidence ?? 0) * 100) }}%</span>
          </div>
          <div class="mt-1 text-[10px] text-gray-600 truncate">{{ d.model_used ?? 'unknown model' }}</div>
        </button>
      </div>

      <!-- Right: inspector -->
      <div v-if="selected" class="flex-1 flex flex-col min-w-0 overflow-hidden">
        <!-- Inspector header -->
        <div class="px-5 py-3 border-b border-surface-700 flex items-center gap-3 flex-shrink-0 bg-surface-900">
          <span
            class="px-2 py-0.5 rounded text-xs font-bold border"
            :class="actionColor(selected.action)"
          >{{ selected.action }}</span>
          <span class="text-sm text-gray-300">Decision #{{ selected.id }}</span>
          <span class="text-xs text-gray-500 tabular-nums">{{ fmt(selected.timestamp) }}</span>
          <div class="ml-auto flex items-center gap-2">
            <span v-if="selected.executed" class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">Executed</span>
            <span v-else-if="selected.execution_error" class="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/25">Error</span>
            <span v-else class="text-[10px] px-1.5 py-0.5 rounded bg-surface-700 text-gray-500 border border-surface-600">Not executed</span>
          </div>
        </div>

        <!-- Tabs -->
        <div class="px-5 pt-3 border-b border-surface-700 flex gap-1 flex-shrink-0 bg-surface-900">
          <button
            v-for="t in (['input', 'output', 'info'] as const)"
            :key="t"
            class="px-3 py-2 text-xs font-medium transition-colors capitalize border-b-2 -mb-px"
            :class="tab === t
              ? 'text-sky-400 border-sky-500'
              : 'text-gray-500 hover:text-gray-300 border-transparent'"
            @click="tab = t"
          >{{ t === 'input' ? 'Prompt' : t === 'output' ? 'Response' : 'Info' }}</button>
        </div>

        <!-- Tab panels -->
        <div class="flex-1 overflow-auto p-5 bg-surface-800">
          <!-- PROMPT -->
          <div v-if="tab === 'input'">
            <div
              v-if="selected.raw_prompt"
              class="bg-surface-900 border border-surface-700 rounded-xl p-4 font-mono text-xs text-gray-300 whitespace-pre-wrap leading-relaxed overflow-auto max-h-[calc(100%-2rem)]"
            >{{ selected.raw_prompt }}</div>
            <div v-else class="text-sm text-gray-600 italic">No prompt recorded for this decision.</div>
          </div>

          <!-- RESPONSE -->
          <div v-else-if="tab === 'output'" class="space-y-4">
            <div class="grid grid-cols-2 gap-3">
              <div class="bg-surface-900 rounded-lg p-3 border border-surface-700">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5">Action</div>
                <span class="px-2 py-0.5 rounded text-sm font-bold border" :class="actionColor(selected.action)">{{ selected.action }}</span>
              </div>
              <div class="bg-surface-900 rounded-lg p-3 border border-surface-700">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5">XRP Amount</div>
                <div class="text-sm text-gray-200 font-mono tabular-nums">
                  {{ selected.xrp_amount != null ? selected.xrp_amount.toFixed(4) : '—' }}
                </div>
              </div>
              <div class="bg-surface-900 rounded-lg p-3 border border-surface-700">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Confidence</div>
                <div class="flex items-center gap-2">
                  <div class="flex-1 bg-surface-700 rounded-full h-1.5 overflow-hidden">
                    <div class="h-1.5 rounded-full bg-sky-500 transition-all" :style="{ width: confidencePct + '%' }"></div>
                  </div>
                  <span class="text-xs text-gray-300 font-mono tabular-nums">{{ confidencePct }}%</span>
                </div>
              </div>
              <div class="bg-surface-900 rounded-lg p-3 border border-surface-700">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5">Tokens</div>
                <div class="text-sm text-gray-200 font-mono tabular-nums">{{ totalTokens.toLocaleString() }}</div>
                <div class="text-[10px] text-gray-600 mt-0.5 font-mono">
                  {{ selected.prompt_tokens ?? 0 }} in · {{ selected.completion_tokens ?? 0 }} out
                </div>
              </div>
            </div>

            <div v-if="selected.reasoning" class="bg-surface-900 rounded-lg p-4 border border-surface-700">
              <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Reasoning</div>
              <p class="text-sm text-gray-300 leading-relaxed">{{ selected.reasoning }}</p>
            </div>

            <div>
              <button
                class="text-xs text-sky-400 hover:text-sky-300 mb-2 flex items-center gap-1 transition-colors"
                @click="showRawResponse = !showRawResponse"
              >
                <svg class="w-3.5 h-3.5 transition-transform duration-150" :class="showRawResponse ? 'rotate-90' : ''" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                Raw response
              </button>
              <div
                v-if="showRawResponse && selected.raw_response"
                class="bg-surface-900 border border-surface-700 rounded-xl p-4 font-mono text-xs text-gray-400 whitespace-pre-wrap leading-relaxed overflow-auto max-h-64"
              >{{ selected.raw_response }}</div>
            </div>
          </div>

          <!-- INFO -->
          <div v-else-if="tab === 'info'">
            <dl class="space-y-0">
              <div
                v-for="row in [
                  { label: 'Decision ID', value: String(selected.id) },
                  { label: 'Model', value: selected.model_used ?? 'unknown' },
                  { label: 'Timestamp', value: fmt(selected.timestamp) },
                  { label: 'Executed', value: selected.executed ? 'Yes' : 'No' },
                  { label: 'Execution error', value: selected.execution_error ?? '—' },
                  { label: 'Prompt tokens', value: selected.prompt_tokens != null ? String(selected.prompt_tokens) : '—' },
                  { label: 'Completion tokens', value: selected.completion_tokens != null ? String(selected.completion_tokens) : '—' },
                  { label: 'Total tokens', value: totalTokens > 0 ? String(totalTokens) : '—' },
                ]"
                :key="row.label"
                class="flex items-center justify-between py-2.5 border-b border-surface-700/60 gap-4 last:border-0"
              >
                <dt class="text-xs text-gray-500">{{ row.label }}</dt>
                <dd
                  class="text-xs font-mono text-right"
                  :class="row.label === 'Execution error' && row.value !== '—' ? 'text-rose-400' : 'text-gray-300'"
                >{{ row.value }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      <!-- Empty right panel -->
      <div
        v-else
        class="flex-1 flex items-center justify-center text-gray-600 text-sm select-none"
      >
        ← Select a decision to inspect
      </div>
    </div>
  </div>
</template>

