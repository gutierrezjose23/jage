<script setup>
import { onMounted, ref } from 'vue'
import { api, session } from '../lib/api.js'
import { dateLabel, money } from '../lib/format.js'
import AccountHeading from '../components/AccountHeading.vue'
import AlertMessage from '../components/AlertMessage.vue'
import ReservationCard from '../components/ReservationCard.vue'
import AppIcon from '../components/AppIcon.vue'
const data = ref({ balance: '0.00', reservations: [], transactions: [], promotions: [] })
const loading = ref(true)
const busy = ref(null)
const error = ref('')
const success = ref('')
const active = ref('trips')
const kinds = {
  adjustment: 'Ajuste de saldo',
  topup: 'Recarga',
  commission: 'Comisión de viaje',
  promotion: 'Bono promocional',
  admin_adjustment: 'Ajuste de saldo',
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await api('/driver/dashboard')
  } catch (cause) {
    error.value = cause.message
  } finally {
    loading.value = false
  }
}
async function redeem(promotion) {
  if (busy.value) return
  busy.value = promotion.id
  error.value = ''
  success.value = ''
  try {
    await api(`/driver/promotions/${promotion.id}/redeem`, { method: 'POST' })
    success.value = `Bono de ${money(promotion.amount)} añadido a tu saldo para comisiones.`
    await load()
  } catch (cause) {
    error.value = cause.message
  } finally {
    busy.value = null
  }
}
onMounted(load)
</script>
<template>
  <section class="page-shell account-page">
    <AccountHeading
      eyebrow="ESPACIO DEL CONDUCTOR"
      :title="`Hola, ${session.user?.first_name || 'conductor'}.`"
      description="Consulta tus viajes asignados, el saldo para comisiones y tus promociones."
    >
      <button
        class="btn btn-outline btn-small"
        :disabled="loading || !!busy"
        @click="load"
      >
        {{ loading ? 'Actualizando…' : 'Actualizar datos' }}
      </button>
    </AccountHeading>
    <AlertMessage :message="error" />
    <AlertMessage
      :message="success"
      type="success"
    />
    <p
      v-if="loading"
      class="loading-state"
      role="status"
    >
      Cargando tu espacio…
    </p>
    <template v-else-if="!error">
      <div class="wallet-panel">
        <div>
          <p class="eyebrow">SALDO PARA COMISIONES</p>
          <p class="wallet-amount">{{ money(data.balance) }}</p>
          <p>Disponible para las comisiones de tus viajes.</p>
        </div>
        <div class="wallet-explainer">
          <AppIcon
            name="wallet"
            :size="28"
          />
          <p>
            La comisión se descuenta una sola vez cuando JAGE marca el viaje como completado.
            Coordina las recargas con administración.
          </p>
          <p class="text-sm">Este saldo no es retirable y la aplicación no procesa pagos.</p>
        </div>
      </div>
      <div
        class="account-tabs"
        aria-label="Secciones del conductor"
      >
        <button
          :class="{ active: active === 'trips' }"
          :aria-pressed="active === 'trips'"
          @click="active = 'trips'"
        >
          Mis viajes
        </button>
        <button
          :class="{ active: active === 'wallet' }"
          :aria-pressed="active === 'wallet'"
          @click="active = 'wallet'"
        >
          Historial de saldo
        </button>
        <button
          :class="{ active: active === 'promotions' }"
          :aria-pressed="active === 'promotions'"
          @click="active = 'promotions'"
        >
          Promociones
        </button>
      </div>
      <div v-if="active === 'trips'">
        <h2 class="panel-title mb-6">Tus viajes asignados</h2>
        <div
          v-if="data.reservations.length"
          class="grid gap-5 lg:grid-cols-2"
        >
          <ReservationCard
            v-for="reservation in data.reservations"
            :key="reservation.id"
            :reservation="reservation"
          >
            <div
              v-if="reservation.user"
              class="driver-client"
            >
              <p class="field-hint">Cliente de este viaje</p>
              <p class="font-semibold">
                {{ reservation.user.first_name }} {{ reservation.user.last_name }}
              </p>
              <a
                v-if="reservation.user.phone"
                :href="`tel:${reservation.user.phone.replace(/[^+\d]/g, '')}`"
                class="text-action"
                :aria-label="`Llamar al cliente: ${reservation.user.phone}`"
              >
                Llamar: {{ reservation.user.phone }}
              </a>
            </div>
            <p class="commission-line">
              Comisión de este viaje:
              <strong>
                {{
                  reservation.commission === null ? 'Por definir' : money(reservation.commission)
                }}
              </strong>
              <span v-if="reservation.commission_charged">· Descontada</span>
            </p>
          </ReservationCard>
        </div>
        <div
          v-else
          class="empty-state"
        >
          <AppIcon
            name="car"
            :size="30"
          />
          <h3>Aún no tienes viajes asignados.</h3>
          <p>JAGE coordinará y asignará los viajes desde administración.</p>
        </div>
      </div>
      <div v-else-if="active === 'wallet'">
        <h2 class="panel-title mb-6">Movimientos de saldo</h2>
        <div
          v-if="data.transactions.length"
          class="ledger"
        >
          <article
            v-for="transaction in data.transactions"
            :key="transaction.id"
            class="ledger-row"
          >
            <div>
              <p class="font-semibold">
                {{ kinds[transaction.kind] || 'Movimiento de saldo' }}
                <span v-if="transaction.reservation_id">
                  · Viaje #{{ transaction.reservation_id }}
                </span>
              </p>
              <p class="muted text-sm break-words">{{ transaction.reason }}</p>
              <p class="field-hint">
                {{ dateLabel(transaction.created_at) }} · Movimiento #{{ transaction.id }}
              </p>
            </div>
            <div class="ledger-values">
              <strong :class="Number(transaction.amount) > 0 ? 'credit' : ''">
                {{ Number(transaction.amount) > 0 ? '+' : '' }}{{ money(transaction.amount) }}
              </strong>
              <span>Saldo: {{ money(transaction.balance_after) }}</span>
            </div>
          </article>
        </div>
        <p
          v-else
          class="empty-state"
        >
          Tu historial está vacío. Las recargas, bonos y comisiones aparecerán aquí.
        </p>
      </div>
      <div v-else>
        <h2 class="panel-title mb-2">Promociones para tu camino</h2>
        <p class="muted mb-6">
          Cada bono puede canjearse una vez y se suma al saldo para comisiones.
        </p>
        <div
          v-if="data.promotions.length"
          class="grid gap-5 md:grid-cols-2 xl:grid-cols-3"
        >
          <article
            v-for="promotion in data.promotions"
            :key="promotion.id"
            class="surface promo-card"
          >
            <span class="promo-amount">+{{ money(promotion.amount) }}</span>
            <h3>{{ promotion.title }}</h3>
            <p class="muted text-sm whitespace-pre-wrap break-words">{{ promotion.description }}</p>
            <p class="field-hint mt-4">Vence: {{ dateLabel(promotion.expires_at) }}</p>
            <button
              class="btn btn-primary w-full mt-5"
              :disabled="promotion.redeemed || !!busy"
              @click="redeem(promotion)"
            >
              {{
                promotion.redeemed
                  ? 'Bono canjeado'
                  : busy === promotion.id
                    ? 'Canjeando…'
                    : 'Canjear bono'
              }}
            </button>
          </article>
        </div>
        <p
          v-else
          class="empty-state"
        >
          No hay promociones disponibles por ahora.
        </p>
      </div>
    </template>
  </section>
</template>
