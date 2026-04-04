import { ref } from 'vue'

export const NUMPAD_KEYS = [1, 2, 3, 4, 5, 6, 7, 8, 9, '', 0, '⌫'] as const

export function usePinPad(pinLength: number, onComplete: (pin: string) => void) {
  const pin = ref('')
  const shaking = ref(false)

  function pressKey(key: string | number) {
    if (key === '⌫') {
      pin.value = pin.value.slice(0, -1)
      return
    }
    if (key === '' || pin.value.length >= pinLength) return
    pin.value += String(key)
    if (pin.value.length === pinLength) {
      onComplete(pin.value)
    }
  }

  function reset() {
    pin.value = ''
  }

  function triggerShake() {
    shaking.value = true
    setTimeout(() => { shaking.value = false }, 600)
  }

  return { pin, shaking, pressKey, reset, triggerShake }
}
