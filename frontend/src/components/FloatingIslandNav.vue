<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'

const route = useRoute()
const settingsStore = useSettingsStore()

const nav = [
  {
    name: 'Home',
    to: '/',
    icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
  },
  {
    name: 'Trades',
    to: '/trades',
    icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
  },
  {
    name: 'AI',
    to: '/ai',
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
  },
  {
    name: 'Monitor',
    to: '/monitor',
    icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  },
  {
    name: 'Test',
    to: '/backtest',
    icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  {
    name: 'Admin',
    to: '/admin',
    icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
  },
]

// Index of currently active nav item
const activeIndex = computed(() => {
  const idx = nav.findIndex(n => n.to === route.path)
  return idx >= 0 ? idx : 0
})

// Island is visible
const visible = ref(false)
onMounted(() => {
  // Slight delay so the spring entry animation is perceptible
  setTimeout(() => { visible.value = true }, 80)
})
</script>

<template>
  <Transition name="island-entry">
    <nav
      v-if="visible"
      class="fixed bottom-5 left-1/2 z-50 md:hidden"
      style="transform: translateX(-50%)"
      aria-label="Mobile navigation"
    >
      <!-- Outer glow ring -->
      <div class="island-glow-ring" />

      <!-- Glass island pill -->
      <div class="island-pill">

        <!-- Sliding amber indicator -->
        <div
          class="island-indicator"
          :style="{ transform: `translateX(calc(${activeIndex} * var(--item-w)))` }"
        />

        <!-- Nav items -->
        <RouterLink
          v-for="(item, idx) in nav"
          :key="item.to"
          :to="item.to"
          class="island-item"
          :class="{ 'island-item-active': route.path === item.to }"
          :aria-label="item.name"
          :aria-current="route.path === item.to ? 'page' : undefined"
        >
          <span class="island-icon-wrap">
            <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
            </svg>
          </span>
          <span class="island-label">{{ item.name }}</span>

          <!-- Admin badge -->
          <span
            v-if="item.name === 'Admin' && settingsStore.isAdmin"
            class="island-admin-dot"
          />
        </RouterLink>

      </div>
    </nav>
  </Transition>
</template>

<style scoped>
/* ── Outer ambient glow ── */
.island-glow-ring {
  position: absolute;
  inset: -6px;
  border-radius: 9999px;
  background: radial-gradient(ellipse at center, rgba(245, 158, 11, 0.12) 0%, transparent 70%);
  pointer-events: none;
  animation: island-breathe 4s ease-in-out infinite;
}

/* ── Main pill container ── */
.island-pill {
  --item-w: 52px;
  position: relative;
  display: flex;
  align-items: center;
  gap: 0;
  padding: 6px 8px;
  border-radius: 9999px;

  /* Liquid-glass background */
  background: rgba(24, 24, 27, 0.72);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);

  /* Layered borders & shadows for depth */
  border: 1px solid rgba(255, 255, 255, 0.10);
  box-shadow:
    0 0 0 0.5px rgba(255, 255, 255, 0.06) inset,
    0 1px 0 rgba(255, 255, 255, 0.08) inset,
    0 12px 40px rgba(0, 0, 0, 0.55),
    0 4px 16px rgba(0, 0, 0, 0.4),
    0 1px 4px rgba(0, 0, 0, 0.3);
}

/* ── Sliding amber indicator behind active item ── */
.island-indicator {
  position: absolute;
  left: 8px;
  top: 6px;
  bottom: 6px;
  width: var(--item-w, 52px);
  border-radius: 9999px;
  background: rgba(245, 158, 11, 0.16);
  border: 1px solid rgba(245, 158, 11, 0.28);
  box-shadow: 0 0 16px rgba(245, 158, 11, 0.2), inset 0 1px 0 rgba(245, 158, 11, 0.2);
  /* Spring slide */
  transition: transform 0.48s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: none;
}

/* ── Individual nav items ── */
.island-item {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  width: var(--item-w, 52px);
  padding: 6px 4px;
  border-radius: 9999px;
  color: rgb(113, 113, 122); /* zinc-500 */
  text-decoration: none;
  /* Spring scale */
  transition:
    color 0.3s ease,
    transform 0.48s cubic-bezier(0.34, 1.56, 0.64, 1);
  -webkit-tap-highlight-color: transparent;
}

.island-item:active {
  transform: scale(0.88);
  transition: transform 0.12s ease;
}

.island-item-active {
  color: rgb(251, 191, 36); /* amber-400 */
  transform: scale(1.08);
}

/* ── Icon wrapper ── */
.island-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: filter 0.3s ease;
}

.island-item-active .island-icon-wrap {
  filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.5));
}

/* ── Label ── */
.island-label {
  font-size: 8px;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1;
  transition: opacity 0.3s ease;
}

.island-item:not(.island-item-active) .island-label {
  opacity: 0.55;
}

/* ── Admin presence dot ── */
.island-admin-dot {
  position: absolute;
  top: 4px;
  right: 8px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgb(245, 158, 11);
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.7);
  animation: island-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
}

/* ── Entry animation ── */
.island-entry-enter-active {
  transition: opacity 0.5s ease, transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.island-entry-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.island-entry-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(24px) scale(0.85);
}
.island-entry-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(16px) scale(0.9);
}

/* ── Keyframes ── */
@keyframes island-breathe {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50%       { opacity: 1;   transform: scale(1.04); }
}

@keyframes island-ping {
  0%   { transform: scale(1);   opacity: 1; }
  75%, 100% { transform: scale(2); opacity: 0; }
}
</style>
