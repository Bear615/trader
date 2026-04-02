<script setup lang="ts">
defineProps<{ value: string }>()
</script>

<template>
  <span class="ticker-wrap">
    <!--
      Ghost: invisible copy that gives the container its natural dimensions
      (width = text width, height = line-height). Stays in normal flow.
    -->
    <span class="ticker-ghost" aria-hidden="true">{{ value }}</span>

    <!--
      Keyed transition: when `value` changes, Vue mounts a new span (enter)
      while unmounting the old one (leave) simultaneously.
    -->
    <Transition name="ticker">
      <span :key="value" class="ticker-inner">{{ value }}</span>
    </Transition>
  </span>
</template>

<style scoped>
/* Container sizes itself from the ghost text */
.ticker-wrap {
  position: relative;
  display: inline-block;
  overflow: hidden;
  vertical-align: bottom;
}

/* Invisible sizer — same text, same inherited styles, zero visual footprint */
.ticker-ghost {
  visibility: hidden;
  user-select: none;
  pointer-events: none;
}

/* The real visible span — always absolutely fills the ghost-sized container */
.ticker-inner {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
}

/* ── Slot-machine transition ──
   New value rolls in from the TOP (like a reel advancing forward).
   Old value exits to the BOTTOM. */
.ticker-enter-active,
.ticker-leave-active {
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.35s ease;
}

/* incoming: start above, land at centre */
.ticker-enter-from {
  transform: translateY(-110%);
  opacity: 0;
}

/* outgoing: fall away downward */
.ticker-leave-to {
  transform: translateY(110%);
  opacity: 0;
}
</style>
