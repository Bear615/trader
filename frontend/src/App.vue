<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { usePriceStore } from '@/stores/price'
import { useSettingsStore } from '@/stores/settings'
import SidebarNav from '@/components/SidebarNav.vue'
import TopBar from '@/components/TopBar.vue'
import SiteLock from '@/components/SiteLock.vue'

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
    <!-- Ambient glow blobs -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden mix-blend-screen" aria-hidden="true">
      <div class="absolute -top-40 left-1/3 w-[600px] h-[600px] rounded-full blur-[140px] bg-sky-500/[0.12] animate-pulse" style="animation-duration: 8s" />
      <div class="absolute -bottom-32 right-1/4 w-[500px] h-[500px] rounded-full blur-[120px] bg-violet-500/[0.1] animate-pulse" style="animation-duration: 12s" />
      <div class="absolute top-1/2 -left-20 w-[300px] h-[300px] rounded-full blur-[100px] bg-indigo-500/[0.1] animate-pulse" style="animation-duration: 10s" />
    </div>

    <!-- Sidebar -->
    <SidebarNav />

    <!-- Main content area -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
      <!-- Topbar -->
      <TopBar />

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto p-6 relative">
        <RouterView v-slot="{ Component }">
          <Transition name="page">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>
