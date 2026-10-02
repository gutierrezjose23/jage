import { nextTick } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { loadSession, session, accountPath } from './lib/api.js'
import HomeView from './views/HomeView.vue'

const legacySections = {
  '#servicios': '/servicios',
  '#como-reservar': '/como-reservar',
  '#contacto': '/contacto',
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView, meta: { title: 'Tu viaje empieza aquí' } },
    {
      path: '/servicios',
      component: HomeView,
      meta: { title: 'Servicios', section: 'servicios' },
    },
    {
      path: '/como-reservar',
      component: HomeView,
      meta: { title: 'Cómo reservar', section: 'como-reservar' },
    },
    {
      path: '/contacto',
      component: HomeView,
      meta: { title: 'Contacto', section: 'contacto' },
    },
    {
      path: '/ingresar',
      component: () => import('./views/AuthView.vue'),
      meta: { title: 'Inicia sesión', guest: true },
    },
    {
      path: '/registro',
      component: () => import('./views/AuthView.vue'),
      meta: { title: 'Crea tu cuenta', guest: true },
    },
    {
      path: '/reservar',
      component: () => import('./views/BookingView.vue'),
      meta: { title: 'Solicita tu reserva', roles: ['passenger'] },
    },
    {
      path: '/mis-reservas',
      component: () => import('./views/ReservationsView.vue'),
      meta: { title: 'Mis reservas', roles: ['passenger'] },
    },
    {
      path: '/administracion',
      component: () => import('./views/AdminView.vue'),
      meta: { title: 'Administración', roles: ['admin'] },
    },
    {
      path: '/conductor',
      component: () => import('./views/DriverView.vue'),
      meta: { title: 'Mi espacio de conductor', roles: ['driver'] },
    },
    {
      path: '/:pathMatch(.*)*',
      component: () => import('./views/NotFoundView.vue'),
      meta: { title: 'Página no encontrada' },
    },
  ],
  async scrollBehavior(to, from, saved) {
    if (saved) return saved
    if (to.meta.section) {
      await nextTick()
      const element = document.getElementById(to.meta.section)
      if (element)
        return {
          el: element,
          top: 100,
          behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
            ? 'auto'
            : 'smooth',
        }
    }
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  if (to.path === '/' && Object.hasOwn(legacySections, to.hash)) {
    return { path: legacySections[to.hash], query: to.query, replace: true }
  }
  await loadSession().catch(() => {})
  if (to.meta.roles && !session.user)
    return { path: '/ingresar', query: { siguiente: to.fullPath } }
  if (to.meta.roles && !to.meta.roles.includes(session.user.role)) return accountPath()
  if (to.meta.guest && session.user) return accountPath()
})
router.afterEach((to) => {
  document.title = `JAGE · ${to.meta.title}`
})
export default router
