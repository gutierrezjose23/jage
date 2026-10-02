import { ref, computed, onScopeDispose } from 'vue'

export const WHATSAPP_NUMBER = '51934613286'
export const whatsappUrl = (message) =>
  `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`

/** A location stays in component memory until the user explicitly applies or shares it. */
export function useLocation() {
  const coordinates = ref(null)
  const loading = ref(false)
  const error = ref('')
  let disposed = false
  const mapUrl = computed(() =>
    coordinates.value
      ? `https://www.google.com/maps?q=${coordinates.value.latitude},${coordinates.value.longitude}`
      : '',
  )
  const label = computed(() =>
    coordinates.value ? `${coordinates.value.latitude}, ${coordinates.value.longitude}` : '',
  )
  onScopeDispose(() => {
    disposed = true
  })

  function requestLocation() {
    if (loading.value) return
    error.value = ''
    coordinates.value = null
    if (!navigator.geolocation) {
      error.value = 'Este navegador no permite obtener la ubicación. Escribe tu origen manualmente.'
      return
    }
    loading.value = true
    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (disposed) return
        coordinates.value = {
          latitude: position.coords.latitude.toFixed(6),
          longitude: position.coords.longitude.toFixed(6),
          accuracy: Math.round(position.coords.accuracy),
        }
        loading.value = false
      },
      (cause) => {
        if (disposed) return
        loading.value = false
        error.value =
          {
            1: 'No se autorizó el acceso a tu ubicación. Puedes escribir el origen manualmente o habilitar el permiso en tu navegador.',
            2: 'No pudimos encontrar tu ubicación. Inténtalo desde otro lugar o escribe el origen manualmente.',
            3: 'La búsqueda de ubicación tardó demasiado. Puedes reintentarlo o escribir el origen manualmente.',
          }[cause.code] || 'No pudimos obtener tu ubicación. Escribe el origen manualmente.'
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 },
    )
  }
  function clearLocation() {
    coordinates.value = null
    error.value = ''
  }
  return { coordinates, loading, error, mapUrl, label, requestLocation, clearLocation }
}
