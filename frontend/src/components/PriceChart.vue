<script setup lang="ts">
import { computed } from 'vue'
import type { PricePoint } from '@/api/types'

const props = defineProps<{
  data: PricePoint[]
  loading?: boolean
}>()

// Palette constants — kept in sync with tailwind.config.js
const THEME = {
  accent: '#38bdf8',  // sky-400
  label:  '#6b7280',  // gray-500
  grid:   '#21262d',  // surface-700
} as const

const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: false },
    zoom: { enabled: true },
    sparkline: { enabled: false },
  },
  stroke: { curve: 'smooth', width: 2, colors: [THEME.accent] },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.25,
      opacityTo: 0.0,
      stops: [0, 100],
      colorStops: [
        { offset: 0, color: THEME.accent, opacity: 0.25 },
        { offset: 100, color: THEME.accent, opacity: 0 },
      ],
    },
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { colors: THEME.label, fontSize: '11px' },
      datetimeUTC: false,
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: { colors: THEME.label, fontSize: '11px' },
      formatter: (v: number) => '$' + v.toFixed(4),
    },
  },
  grid: {
    borderColor: THEME.grid,
    strokeDashArray: 4,
    xaxis: { lines: { show: false } },
  },
  tooltip: {
    x: { format: 'dd MMM HH:mm:ss' },
    y: { formatter: (v: number) => '$' + v.toFixed(6) },
  },
  dataLabels: { enabled: false },
  markers: { size: 0 },
}))

const series = computed(() => [
  {
    name: 'XRP/USD',
    data: props.data.map((p) => [new Date(p.timestamp).getTime(), p.price]),
  },
])
</script>

<template>
  <div class="relative">
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-surface-800/60 rounded-lg z-10">
      <div class="w-6 h-6 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
    </div>
    <div v-if="data.length === 0 && !loading" class="h-48 flex items-center justify-center">
      <p class="text-sm text-gray-600">No price data yet. Waiting for DIA poll…</p>
    </div>
    <apexchart
      v-else
      type="area"
      height="260"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>
