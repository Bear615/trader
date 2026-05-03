<script setup lang="ts">
import type { AIDecision } from '@/api/types'
import { ref, computed } from 'vue'

const props = defineProps<{
  decision: AIDecision
  compact?: boolean
  index?: number
}>()

const showRaw = ref(false)

const cfg = computed(() => {
  if (props.decision.action === 'BUY') {
    return {
      text: 'text-emerald-300',
      bg: 'bg-emerald-500/[0.08]',
      border: 'border-emerald-400/25',
      bar: 'bg-emerald-400',
      pill: 'border-emerald-400/25 bg-emerald-500/10 text-emerald-300',
      dot: 'bg-emerald-400',
    }
  }
  if (props.decision.action === 'SELL') {
    return {
      text: 'text-rose-300',
      bg: 'bg-rose-500/[0.08]',
      border: 'border-rose-400/25',
      bar: 'bg-rose-400',
      pill: 'border-rose-400/25 bg-rose-500/10 text-rose-300',
      dot: 'bg-rose-400',
    }
  }
  return {
    text: 'text-slate-300',
    bg: 'bg-slate-500/[0.06]',
    border: 'border-slate-500/30',
    bar: 'bg-blue-400',
    pill: 'border-slate-500/30 bg-slate-500/10 text-slate-300',
    dot: 'bg-blue-400',
  }
})

const pct = computed(() => Math.round((props.decision.confidence ?? 0) * 100))

function fmtTime(ts: string) {
  const d = new Date(ts)
  const diff = Date.now() - d.getTime()
  if (diff < 60_000) return 'Just now'
  if (diff < 3_600_000) return Math.floor(diff / 60_000) + 'm ago'
  if (diff < 86_400_000) return Math.floor(diff / 3_600_000) + 'h ago'
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })
}
</script>

<template>
  <div
    v-if="compact"
    class="flex items-center gap-3 rounded-xl border px-4 py-2.5 transition"
    :class="[cfg.bg, cfg.border]"
  >
    <div class="h-2 w-2 flex-shrink-0 rounded-full" :class="cfg.dot" />
    <span class="text-sm font-medium text-slate-300">{{ decision.action }}</span>
    <span class="ml-auto text-xs text-slate-500">{{ fmtTime(decision.timestamp) }}</span>
  </div>

  <div
    v-else
    class="panel overflow-hidden p-0"
    :class="cfg.border"
  >
    <div class="p-5">
      <div class="flex flex-wrap items-center gap-3">
        <span class="rounded-lg border px-3 py-1 text-xs font-bold tracking-wide" :class="cfg.pill">
          {{ decision.action }}
        </span>

        <span class="font-mono text-sm font-semibold tabular-nums text-slate-100">
          {{ decision.xrp_amount ? decision.xrp_amount.toFixed(4) + ' XRP' : '-' }}
        </span>

        <span v-if="decision.model_used" class="rounded-md border border-slate-700/55 bg-slate-950/35 px-2 py-1 font-mono text-[11px] text-slate-500">
          {{ decision.model_used }}
        </span>

        <div class="min-w-0 flex-1" />

        <div class="flex items-center gap-2">
          <span class="font-mono text-xs font-bold tabular-nums" :class="cfg.text">{{ pct }}%</span>
          <div class="h-1.5 w-24 overflow-hidden rounded-full bg-slate-800">
            <div class="h-full rounded-full transition-all duration-500" :class="cfg.bar" :style="{ width: pct + '%' }" />
          </div>
        </div>

        <span class="text-xs text-slate-500">{{ fmtTime(decision.timestamp) }}</span>

        <span v-if="decision.executed" class="badge-ai">Executed</span>
        <span v-else-if="decision.execution_error" class="badge-sell" :title="decision.execution_error">Failed</span>
      </div>

      <p v-if="decision.reasoning" class="mt-4 border-l-2 border-slate-700/70 pl-3 text-sm leading-relaxed text-slate-400">
        {{ decision.reasoning }}
      </p>

      <div v-if="decision.prompt_tokens || decision.raw_prompt" class="mt-4 flex items-center gap-4 border-t border-slate-700/45 pt-4">
        <div v-if="decision.prompt_tokens" class="font-mono text-xs text-slate-500">
          {{ decision.prompt_tokens.toLocaleString() }} in / {{ decision.completion_tokens?.toLocaleString() ?? '-' }} out
        </div>
        <div class="flex-1" />
        <button
          v-if="decision.raw_prompt"
          @click="showRaw = !showRaw"
          class="text-xs font-medium text-blue-400 transition hover:text-blue-300"
        >
          {{ showRaw ? 'Hide' : 'View' }} raw prompt
        </button>
      </div>

      <Transition
        enter-active-class="transition duration-200"
        enter-from-class="opacity-0 -translate-y-1"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-150"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-1"
      >
        <pre
          v-if="showRaw && decision.raw_prompt"
          class="mt-4 max-h-60 overflow-auto whitespace-pre-wrap rounded-xl border border-slate-700/55 bg-slate-950/55 p-4 font-mono text-xs leading-relaxed text-slate-400"
        >{{ decision.raw_prompt }}</pre>
      </Transition>
    </div>
  </div>
</template>
