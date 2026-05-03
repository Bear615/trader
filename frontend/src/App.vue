<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterView } from 'vue-router'
import { usePriceStore } from '@/stores/price'
import { useSettingsStore } from '@/stores/settings'
import SidebarNav from '@/components/SidebarNav.vue'
import TopBar from '@/components/TopBar.vue'
import SiteLock from '@/components/SiteLock.vue'
import FloatingIslandNav from '@/components/FloatingIslandNav.vue'

const SESSION_KEY = 'site_unlocked'
const siteUnlocked = ref(!!sessionStorage.getItem(SESSION_KEY))
const checkingSession = ref(siteUnlocked.value)
function onUnlocked() { siteUnlocked.value = true }

const priceStore = usePriceStore()
const settingsStore = useSettingsStore()

async function initializeUnlockedApp() {
  await priceStore.fetchCurrent()
  priceStore.connectWebSocket()
}

onMounted(async () => {
  if (siteUnlocked.value) {
    const valid = settingsStore.isAdmin ? await settingsStore.verifySession() : false
    if (!valid) {
      siteUnlocked.value = false
      sessionStorage.removeItem(SESSION_KEY)
      checkingSession.value = false
      return
    }
    await initializeUnlockedApp()
  }
  checkingSession.value = false
})

watch(siteUnlocked, async (unlocked, wasUnlocked) => {
  if (unlocked && !wasUnlocked) {
    await initializeUnlockedApp()
  }
  if (!unlocked && wasUnlocked) {
    priceStore.disconnect()
  }
})

onUnmounted(() => {
  priceStore.disconnect()
})
</script>

<template>
  <div v-if="checkingSession" class="h-screen bg-[#050a12]" />
  <SiteLock v-else-if="!siteUnlocked" @unlocked="onUnlocked" />

  <div v-else class="app-shell">
    <SidebarNav class="hidden md:flex" />

    <div class="app-main">
      <TopBar />

      <main class="content-area">
        <RouterView v-slot="{ Component }">
          <Transition name="page">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>

    <FloatingIslandNav />
  </div>
</template>
