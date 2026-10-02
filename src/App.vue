<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, session, accountPath } from './lib/api.js'
import AppIcon from './components/AppIcon.vue'
import AlertMessage from './components/AlertMessage.vue'
const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)
const busy = ref(false)
const error = ref('')
const roleLabel = computed(
  () =>
    ({ passenger: 'Mis reservas', driver: 'Mi espacio', admin: 'Administración' })[
      session.user?.role
    ],
)
watch(
  () => route.fullPath,
  async (_, previous) => {
    menuOpen.value = false
    error.value = ''
    if (previous) {
      await nextTick()
      const target = document.getElementById(route.meta.section || 'main-content')
      ;(target || document.getElementById('main-content'))?.focus({
        preventScroll: true,
      })
    }
  },
)
function skipToContent() {
  const content = document.getElementById('main-content')
  content?.focus({ preventScroll: true })
  content?.scrollIntoView({ block: 'start' })
}
async function logout() {
  busy.value = true
  error.value = ''
  try {
    await api('/auth/logout', { method: 'POST' })
    session.user = null
    await router.push('/')
  } catch (cause) {
    error.value = cause.message
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <VApp>
    <a
      class="skip-link"
      href="#main-content"
      @click.prevent="skipToContent"
    >
      Saltar al contenido
    </a>
    <header class="site-header">
      <div class="nav-shell">
        <RouterLink
          to="/"
          class="brand"
          aria-label="JAGE, inicio"
        >
          JAGE
          <span class="brand-dot" />
          <span class="brand-caption">VAMOS CONTIGO</span>
        </RouterLink>
        <nav
          class="desktop-nav"
          aria-label="Navegación principal"
        >
          <RouterLink to="/servicios">Servicios</RouterLink>
          <RouterLink to="/como-reservar">Cómo reservar</RouterLink>
          <RouterLink to="/contacto">Contacto</RouterLink>
        </nav>
        <div class="desktop-account">
          <template v-if="session.user">
            <RouterLink
              :to="accountPath()"
              class="btn btn-primary btn-small"
            >
              {{ roleLabel }}
              <AppIcon :size="16" />
            </RouterLink>
            <button
              class="text-action"
              :disabled="busy"
              @click="logout"
            >
              {{ busy ? 'Saliendo…' : 'Salir' }}
            </button>
          </template>
          <template v-else>
            <RouterLink
              to="/ingresar"
              class="nav-login"
            >
              Iniciar sesión
            </RouterLink>
            <RouterLink
              to="/reservar"
              class="btn btn-primary btn-small"
            >
              Reservar
              <AppIcon :size="16" />
            </RouterLink>
          </template>
        </div>
        <button
          class="menu-button"
          :aria-expanded="menuOpen"
          aria-controls="mobile-menu"
          :aria-label="menuOpen ? 'Cerrar menú' : 'Abrir menú'"
          @click="menuOpen = !menuOpen"
        >
          <AppIcon :name="menuOpen ? 'close' : 'menu'" />
        </button>
      </div>
      <nav
        v-if="menuOpen"
        id="mobile-menu"
        class="mobile-menu"
        aria-label="Navegación móvil"
        @keydown.esc="menuOpen = false"
      >
        <RouterLink to="/">Inicio</RouterLink>
        <RouterLink to="/servicios">Servicios</RouterLink>
        <RouterLink to="/como-reservar">Cómo reservar</RouterLink>
        <RouterLink to="/contacto">Contacto</RouterLink>
        <template v-if="session.user">
          <RouterLink :to="accountPath()">{{ roleLabel }}</RouterLink>
          <button
            :disabled="busy"
            @click="logout"
          >
            Cerrar sesión
          </button>
        </template>
        <template v-else>
          <RouterLink to="/ingresar">Iniciar sesión</RouterLink>
          <RouterLink to="/registro">Crear cuenta</RouterLink>
          <RouterLink to="/reservar">Solicitar reserva ↗</RouterLink>
        </template>
      </nav>
    </header>
    <div
      v-if="error"
      class="page-shell pt-4"
    >
      <AlertMessage :message="error" />
    </div>
    <main
      id="main-content"
      tabindex="-1"
    >
      <RouterView />
    </main>
    <footer class="site-footer">
      <div class="page-shell">
        <div class="footer-top">
          <RouterLink
            to="/"
            class="brand"
          >
            JAGE
            <span class="brand-dot" />
          </RouterLink>
          <p>De Huaral a tu próximo destino.</p>
          <a
            href="https://wa.me/51934613286"
            target="_blank"
            rel="noopener noreferrer"
          >
            +51 934 613 286
            <AppIcon :size="16" />
          </a>
        </div>
        <div class="footer-bottom">
          <span>© {{ new Date().getFullYear() }} JAGE · Huaral, Perú</span>
          <span>Viajes privados · Huaral–Lima · Aeropuerto</span>
        </div>
      </div>
    </footer>
  </VApp>
</template>
