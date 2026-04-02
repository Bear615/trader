<script setup lang="ts">
import type { AIDecision } from '@/api/types'
import { ref, computed } from 'vue'

const props = defineProps<{
  decision: AIDecision
  compact?: boolean
  index?: number
}>()

const showRaw = ref(false)

const isBuy  = computed(() => props.decision.action === 'BUY')
const isSell = computed(() => props.decision.action === 'SELL')

const cfg = computed(() => {
  if (isBuy.value)  return { text: 'text-emerald-400', bg: 'bg-emerald-500/[0.08]', border: 'border-emerald-500/20', bar: 'bg-emerald-400', accent: '#10b981', pill: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30', dot: 'bg-emerald-400' }
  if (isSell.value) return { text: 'text-rose-400',    bg: 'bg-rose-500/[0.08]',    border: 'border-rose-500/20',    bar: 'bg-rose-400',    accent: '#f43f5e', pill: 'bg-rose-500/15 text-rose-300 border border-rose-500/30',    dot: 'bg-rose-400'    }
  return                   { text: 'text-slate-400',   bg: 'bg-slate-500/[0.06]',   border: 'border-slate-600/20',   bar: 'bg-slate-500',   accent: '#475569', pill: 'bg-slate-500/15 text-slate-300 border border-slate-600/30',   dot: 'bg-slate-500'   }
})

const pct = computed(() => Math.round(props.decision.confidence * 100))

function fmtTime(ts: string) {
  const d = new Date(ts)
  const diff = Date.now() - d.getTime()
  if (diff < 60_000)     return 'just now'
  if (diff < 3_600_000)  return Math.floor(diff / 60_000) + 'm ago'
  if (diff < 86_400_000) return Math.floor(diff / 3_600_000) + 'h ago'
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })
}
</script>

<template>
  <!-- COMPACT MODE (used by AI Monitor sidebar) -->
  <div
    v-if="compact"
    class="flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-all duration-300 hover:-translate-y-0.5"
    :class="[cfg.bg, cfg.border]"
  >
    <div class="w-2 h-2 rounded-full flex-shrink-0 animate-pulse" :class="cfg.dot" />
    <span :class="['text-xs font-black tracking-widest', cfg.text]">{{ decision.action }}</span>
    <span class="text-xs text-gray-400 font-mono ml-auto">{{ fmtTime(decision.timestamp) }}</span>
  </div>

  <!-- FULL MODE -->
  <div
    v-else
    class="group relative rounded-2xl border bg-white/[0.025] overflow-hidden transition-all duration-300 hover:-translate-y-0.5 hover:bg-white/[0.04]"
    :class="cfg.border"
  >
    <!-- Left accent bar -->
    <div class="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-2xl" :style="{ background: cfg.accent }" />

    <div class="pl-6 pr-5 py-4 space-y-3">

      <!-- ── Main row ── -->
      <div class="flex items-center gap-3 flex-wrap">
        <!-- Action pill -->
        <span class="text-[11px] font-black tracking-[0.15em] px-3 py-1 rounded-lg" :class="cfg.pill">
          {{ decision.action }}
        </span>

        <!-- XRP amount -->
        <span class="text-sm font-bold font-mono tabular-nums text-gray-100">
          {{ decision.xrp_amount ? decision.xrp_amount.toFixed(4) + ' XRP' : '—' }}
        </span>

        <!-- Model chip -->
        <span v-if="decision.model_used" class="text-[10px] font-mono text-gray-600 bg-white/[0.04] border border-white/[0.06] px-2 py-0.5 rounded-md">
          {{ decision.model_used }}
        </span>

        <div class="flex-1 min-w-0" />

        <!-- Confidence bar + percentage -->
        <div class="flex items-center gap-2 shrink-0">
          <span class="text-xs font-bold tabular-nums font-mono" :class="cfg.text">{{ pct }}%</span>
          <div class="w-20 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-700"
              :class="cfg.bar"
              :style="{ width: pct + '%' }"
            />
          </div>
        </div>

        <!-- Timestamp -->
        <span class="text-xs text-gray-600 tabular-nums shrink-0">{{ fmtTime(decision.timestamp) }}</span>

        <!-- Status badge -->
        <span
          v-if="decision.executed"
          class="flex items-center gap-1 text-[10px] font-semibold text-sky-400 bg-sky-500/10 border border-sky-500/20 px-2 py-0.5 rounded-full shrink-0"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Executed
        </span>
        <span
          v-else-if="decision.execution_error"
          class="flex items-center gap-1 text-[10px] font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full shrink-0"
          :title="decision.execution_error"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Failed
        </span>
        <span
          v-else-if="decision.action !== 'HOLD'"
          class="text-[10px] text-gray-700 font-medium px-2 py-0.5 bg-white/[0.03] border border-white/[0.05] rounded-full shrink-0"
        >
          Skipped
        </span>
      </div>

      <!-- ── Reasoning ── -->
      <p
        v-if="decision.reasoning"
        class="text-sm text-gray-400 leading-relaxed border-l-2 border-white/[0.07] pl-3 italic"
      >
        {{ decision.reasoning }}
      </p>

      <!-- ── Footer: tokens + raw prompt toggle ── -->
      <div
        v-if="decision.prompt_tokens || decision.raw_prompt"
        class="flex items-center gap-4 pt-2 border-t border-white/[0.05]"
      >
        <div v-if="decision.prompt_tokens" class="flex items-center gap-2">
          <span class="text-[10px] uppercase tracking-wider text-gray-700">Tokens</span>
          <span class="text-[11px] font-mono text-sky-600/80">{{ decision.prompt_tokens.toLocaleString() }} in</span>
          <span class="text-gray-700 text-[10px]">·</span>
          <span class="text-[11px] font-mono text-violet-600/80">{{ decision.completion_tokens?.toLocaleString() ?? '—' }} out</span>
        </div>
        <div class="flex-1" />
        <button
          v-if="decision.raw_prompt"
          @click="showRaw = !showRaw"
          class="flex items-center gap-1.5 text-[11px] text-gray-600 hover:text-gray-300 transition-colors"
        >
          <svg
            class="w-3 h-3 transition-transform duration-200"
            :class="showRaw ? 'rotate-180' : ''"
            fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
          {{ showRaw ? 'Hide' : 'View' }} raw prompt
        </button>
      </div>

      <!-- ── Raw prompt ── -->
      <Transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0 -translate-y-1"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition-all duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-1"
      >
        <pre
          v-if="showRaw && decision.raw_prompt"
          class="text-[11px] text-gray-500 bg-black/40 border border-white/[0.06] rounded-xl p-4 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-60"
        >{{ decision.raw_prompt }}</pre>
      </Transition>

    </div>
  </div>
</template>
