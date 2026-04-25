import { reactive } from 'vue'

const state = reactive({
  toasts: [],
})

let toastCounter = 0

function removeToast(id) {
  const index = state.toasts.findIndex((toast) => toast.id === id)
  if (index >= 0) {
    state.toasts.splice(index, 1)
  }
}

function showToast(message, type = 'success', duration = 2600) {
  const id = ++toastCounter
  state.toasts.push({ id, message, type })

  window.setTimeout(() => {
    removeToast(id)
  }, duration)
}

export function useToast() {
  return {
    toasts: state.toasts,
    removeToast,
    showToast,
    showSuccess(message) {
      showToast(message, 'success')
    },
    showError(message) {
      showToast(message, 'error', 3400)
    },
    showWarning(message) {
      showToast(message, 'warning', 3000)
    },
  }
}