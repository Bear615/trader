<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { usePriceStore } from '@/stores/price'
import { useSettingsStore } from '@/stores/settings'
import SidebarNav from '@/components/SidebarNav.vue'
import TopBar from '@/components/TopBar.vue'
import SiteLock from '@/components/SiteLock.vue'
import FloatingIslandNav from '@/components/FloatingIslandNav.vue'

const SESSION_KEY = 'site_unlocked'
const siteUnlocked = ref(!!sessionStorage.getItem(SESSION_KEY))
function onUnlocked() { siteUnlocked.value = true }

const priceStore = usePriceStore()
const settingsStore = useSettingsStore()

onMounted(async () => {
  await priceStore.fetchCurrent()
  priceStore.connectWebSocket()
  // Pre-load settings so TopBar mode badge works without visiting Admin
  if (settingsStore.isAdmin) {
    settingsStore.fetchSettings().catch(() => {/* ignore if key expired */})
  }
})

onUnmounted(() => {
  priceStore.disconnect()
})
</script>

<template>
  <SiteLock v-if="!siteUnlocked" @unlocked="onUnlocked" />

  <div v-else class="flex h-screen bg-surface-950 overflow-hidden relative">
    <!-- Subtle dot-grid texture — static, zero JS cost -->
    <div
      class="absolute inset-0 pointer-events-none"
      aria-hidden="true"
      style="background-image: radial-gradient(circle, #27272a 1px, transparent 1px); background-size: 28px 28px; opacity: 0.5;"
    />

    <!-- Sidebar (desktop only) -->
    <SidebarNav class="hidden md:flex" />

    <!-- Main content area -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
      <!-- Topbar -->
      <TopBar />

      <!-- Page content — extra bottom padding on mobile for floating island -->
      <main class="flex-1 overflow-y-auto p-4 md:p-6 pb-28 md:pb-6 relative">
        <RouterView v-slot="{ Component }">
          <Transition name="page">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>

    <!-- Floating Island nav (mobile only) -->
    <FloatingIslandNav />
  </div>
</template>
