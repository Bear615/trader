<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { SettingMeta } from '@/api/types'

const props = defineProps<{
  settingKey: string
  value: unknown
  meta?: SettingMeta
  status?: 'idle' | 'saving' | 'saved' | 'error'
}>()

const emit = defineEmits<{
  save: [value: unknown]
}>()

const local = ref(props.value)

watch(() => props.value, (v) => { local.value = v })

const PROVIDER_PRESETS: Record<string, string> = {
  openai: '',
  ollama: 'http://localhost:11434/api',
  groq: 'https://api.groq.com/openai/v1',
  together: 'https://api.together.xyz/v1',
  openrouter: 'https://openrouter.ai/api/v1',
  'lm-studio': 'http://localhost:1234/v1',
  custom: '',
}

const type = computed(() => {
  const d = props.meta?.default
  if (props.settingKey === 'ai_system_prompt') return 'textarea'
  if (props.settingKey === 'ai_provider_preset') return 'select-provider'
  if (props.settingKey === 'ai_api_key') return 'password'
  if (typeof d === 'boolean') return 'toggle'
  if (typeof d === 'number') return 'number'
  if (props.settingKey.includes('timeframe')) return 'select-timeframe'
  return 'text'
})

const providerBaseUrlPreview = computed(() => {
  if (type.value !== 'select-provider') return ''
  const preset = String(local.value)
  const url = PROVIDER_PRESETS[preset]
  return url ? url : 'https://api.openai.com/v1 (default)'
})

const isModified = computed(() => {
  if (type.value === 'number') return Number(local.value) !== Number(props.value)
  return local.value !== props.value
})

function handleSave() {
  let val: unknown = local.value
  if (type.value === 'number') val = Number(local.value)
  if (type.value === 'toggle') val = Boolean(local.value)
  emit('save', val)
}

function handleToggle() {
  local.value = !local.value
  emit('save', local.value)
}

const ACRONYMS = new Set(['ai', 'api', 'url', 'id', 'usd', 'xrp', 'ui'])

const label = computed(() => {
  return props.settingKey
    .split('_')
    .map((word) => {
      const lower = word.toLowerCase()
      return ACRONYMS.has(lower) ? lower.toUpperCase() : word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    })
    .join(' ')
})

const statusIcon = computed(() => {
  if (props.status === 'saving') return 'spin'
  if (props.status === 'saved') return 'check'
  if (props.status === 'error') return 'x'
  return null
})

const statusColor = computed(() => {
  if (props.status === 'saved') return 'text-emerald-400'
  if (props.status === 'error') return 'text-rose-400'
  return 'text-sky-400'
})
</script>

<template>
  <!-- Textarea fields get a full-width stacked layout; all others use the side-by-side row -->
  <div
    :class="[
      'py-4 border-b last:border-0',
      'border-white/[0.06]',
      type === 'textarea'
        ? 'flex flex-col gap-3'
        : 'flex items-start justify-between gap-6'
    ]"
  >
    <!-- Label + description -->
    <div :class="type === 'textarea' ? '' : 'flex-1 min-w-0'">
      <div class="text-sm font-medium text-gray-200">{{ label }}</div>
      <div v-if="meta?.description" class="text-xs text-gray-500 mt-0.5 leading-relaxed">{{ meta.description }}</div>
    </div>

    <!-- Control -->
    <div :class="type === 'textarea' ? 'w-full' : 'flex-shrink-0 flex items-center gap-2'">
      <!-- Toggle -->
      <template v-if="type === 'toggle'">
        <button
          @click="handleToggle"
          :class="[
            'toggle-track',
            local ? 'bg-sky-600' : 'bg-surface-600'
          ]"
          role="switch"
          :aria-checked="local ? 'true' : 'false'"
        >
          <span
            :class="['toggle-thumb', local ? 'translate-x-5' : 'translate-x-0']"
          />
        </button>
        <span :class="['text-xs font-medium', local ? 'text-sky-400' : 'text-gray-500']">
          {{ local ? 'ON' : 'OFF' }}
        </span>
      </template>

      <!-- Textarea — full-width, stacked -->
      <template v-else-if="type === 'textarea'">
        <div class="flex flex-col gap-2 w-full">
          <textarea
            v-model="local as string"
            class="textarea text-xs font-mono leading-relaxed min-h-[160px] w-full"
          />
          <div class="flex items-center justify-end gap-2">
            <span v-if="status === 'saved'" class="text-xs text-emerald-400 flex items-center gap-1">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Saved
            </span>
            <span v-if="status === 'error'" class="text-xs text-rose-400">Failed to save</span>
            <button
              @click="handleSave"
              :disabled="!isModified || status === 'saving'"
              :class="['btn btn-primary btn-sm', !isModified ? 'opacity-40' : '']"
            >
              <div v-if="status === 'saving'" class="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
              Save
            </button>
          </div>
        </div>
      </template>

      <!-- Select (provider preset) -->
      <template v-else-if="type === 'select-provider'">
        <div class="flex flex-col gap-1.5 items-end">
          <select v-model="local" class="select w-40" @change="handleSave">
            <option v-for="(url, name) in PROVIDER_PRESETS" :key="name" :value="name">
              {{ name }}
            </option>
          </select>
          <span class="text-[10px] text-gray-600 font-mono truncate max-w-[220px]" :title="providerBaseUrlPreview">
            {{ providerBaseUrlPreview }}
          </span>
        </div>
      </template>

      <!-- Select (timeframe) -->
      <template v-else-if="type === 'select-timeframe'">
        <select v-model="local" class="select w-28" @change="handleSave">
          <option v-for="tf in ['1h','6h','24h','7d','30d']" :key="tf" :value="tf">{{ tf }}</option>
        </select>
      </template>

      <!-- Number / Text / Password -->
      <template v-else>
        <div class="flex items-center gap-2">
          <input
            v-model="local"
            :type="type === 'password' ? 'password' : (type === 'number' ? 'number' : 'text')"
            :step="type === 'number' ? 'any' : undefined"
            class="input w-36 text-right font-mono text-sm"
            @keyup.enter="handleSave"
          />
          <button
            @click="handleSave"
            :disabled="!isModified || status === 'saving'"
            :class="['btn btn-sm', isModified ? 'btn-primary' : 'btn-ghost opacity-40']"
          >
            <div v-if="status === 'saving'" class="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
            <svg v-else-if="status === 'saved'" class="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else-if="status === 'error'" class="w-3.5 h-3.5 text-rose-400" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span v-else>Save</span>
          </button>
        </div>
      </template>
    </div>
  </div>
</template>
