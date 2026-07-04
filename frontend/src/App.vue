<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { usePriceStore } from '@/stores/price'
import { useSettingsStore } from '@/stores/settings'
import SidebarNav from '@/components/SidebarNav.vue'
import TopBar from '@/components/TopBar.vue'
import SiteLock from '@/components/SiteLock.vue'
import FloatingIslandNav from '@/components/FloatingIslandNav.vue'

const priceStore = usePriceStore()
const settingsStore = useSettingsStore()
const route = useRoute()
const router = useRouter()

// Single source of truth: the app is unlocked iff we hold an admin session.
// This is the same flag the router guard uses, so the UI gate and the route
// guard can never disagree (which previously caused a redirect loop).
const siteUnlocked = computed(() => settingsStore.isAdmin)
const checkingSession = ref(siteUnlocked.value)

async function initializeUnlockedApp() {
  await priceStore.fetchCurrent()
  priceStore.connectWebSocket()
}

function onUnlocked() {
  // While locked, the router guard parks navigation on /admin. Now that the
  // session is valid, send the user to where they were originally headed.
  const redirect = route.query.redirect as string | undefined
  router.replace(redirect ? { name: redirect } : { name: 'dashboard' }).catch(() => {})
}

onMounted(async () => {
  if (siteUnlocked.value) {
    const valid = await settingsStore.verifySession()
    if (!valid) {
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
