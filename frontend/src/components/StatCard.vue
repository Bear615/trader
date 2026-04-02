<script setup lang="ts">
import NumberTicker from './NumberTicker.vue'

defineProps<{
  label: string
  value: string
  valueClass?: string
  sub?: string
}>()
</script>

<template>
  <div class="card">
    <div class="stat-label">{{ label }}</div>
    <div :class="['stat-value mt-2', valueClass ?? 'text-gray-100']">
      <NumberTicker :value="value" />
    </div>
    <div v-if="sub" class="text-xs text-gray-500 mt-1.5">{{ sub }}</div>
  </div>
</template>
