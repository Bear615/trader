<script setup lang="ts">
import { computed } from 'vue'
import type { PricePoint } from '@/api/types'
import { formatCurrency } from '@/utils/format'

const props = defineProps<{
  data: PricePoint[]
  loading?: boolean
  quoteCurrency?: string
}>()

const THEME = {
  blue: '#3b82f6',
  blueSoft: '#60a5fa',
  label: '#8b98aa',
  grid: 'rgba(148, 163, 184, 0.13)',
} as const

const chartPoints = computed(() =>
  props.data
    .map((p) => ({ time: new Date(p.timestamp).getTime(), price: Number(p.price) }))
    .filter((p) => Number.isFinite(p.time) && Number.isFinite(p.price))
    .sort((a, b) => a.time - b.time),
)

const valueBounds = computed(() => {
  const prices = chartPoints.value.map((p) => p.price)
  if (!prices.length) return undefined

  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min
  const fallbackPadding = Math.max(Math.abs(max) * 0.015, 0.0005)
  const padding = range > 0 ? Math.max(range * 0.18, fallbackPadding) : fallbackPadding

  return {
    min: Math.max(0, min - padding),
    max: max + padding,
  }
})

const timeBounds = computed(() => {
  const points = chartPoints.value
  if (!points.length) return undefined
  if (points.length === 1) {
    const padding = 5 * 60 * 1000
    return {
      min: points[0].time - padding,
      max: points[0].time + padding,
    }
  }
  return {
    min: points[0].time,
    max: points[points.length - 1].time,
  }
})

const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: false },
    zoom: { enabled: true },
    fontFamily: 'Inter, ui-sans-serif, system-ui',
  },
  stroke: { curve: 'stepline', width: 2, colors: [THEME.blueSoft] },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 0.8,
      opacityFrom: 0.34,
      opacityTo: 0.02,
      stops: [0, 92],
      colorStops: [
        { offset: 0, color: THEME.blue, opacity: 0.34 },
        { offset: 100, color: THEME.blue, opacity: 0.02 },
      ],
    },
  },
  xaxis: {
    type: 'datetime',
    min: timeBounds.value?.min,
    max: timeBounds.value?.max,
    labels: {
      style: { colors: THEME.label, fontSize: '12px', fontWeight: 500 },
      datetimeUTC: false,
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
    tooltip: { enabled: false },
  },
  yaxis: {
    min: valueBounds.value?.min,
    max: valueBounds.value?.max,
    tickAmount: 4,
    forceNiceScale: false,
    decimalsInFloat: 4,
    labels: {
      style: { colors: THEME.label, fontSize: '12px', fontWeight: 500 },
      formatter: (v: number) => formatCurrency(v, props.quoteCurrency, 4),
    },
  },
  grid: {
    borderColor: THEME.grid,
    strokeDashArray: 3,
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } },
    padding: { top: 6, right: 16, bottom: 0, left: 8 },
  },
  tooltip: {
    x: { format: 'dd MMM HH:mm:ss' },
    y: { formatter: (v: number) => formatCurrency(v, props.quoteCurrency, 6) },
  },
  dataLabels: { enabled: false },
  markers: { size: 0 },
}))

const series = computed(() => [
  {
    name: `XRP/${props.quoteCurrency ?? 'GBP'}`,
    data: chartPoints.value.map((p) => [p.time, p.price]),
  },
])
</script>

<template>
  <div class="relative min-h-[285px]">
    <div v-if="loading" class="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-slate-950/50 backdrop-blur-sm">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
    </div>

    <div v-if="data.length === 0 && !loading" class="flex h-[285px] items-center justify-center rounded-xl border border-slate-700/40 bg-slate-950/25">
      <p class="text-sm text-slate-500">No price data yet. Waiting for the next price poll.</p>
    </div>

    <apexchart
      v-else
      type="area"
      height="300"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>
