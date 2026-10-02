<script setup>
import AppIcon from './AppIcon.vue'
import StatusBadge from './StatusBadge.vue'
import { services, dateLabel, timeLabel } from '../lib/format.js'
defineProps({ reservation: { type: Object, required: true } })
</script>
<template>
  <article class="reservation-card">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <span class="eyebrow muted">SOLICITUD #{{ reservation.id }}</span>
      <StatusBadge :status="reservation.status" />
    </div>
    <h3 class="mt-5 mb-5">{{ services[reservation.service] || reservation.service }}</h3>
    <div class="journey">
      <div>
        <span class="journey-dot" />
        <div>
          <p class="field-hint">Origen</p>
          <p>{{ reservation.origin }}</p>
        </div>
      </div>
      <div>
        <span class="journey-dot destination" />
        <div>
          <p class="field-hint">Destino</p>
          <p>{{ reservation.destination }}</p>
        </div>
      </div>
    </div>
    <div class="reservation-meta">
      <span>
        <AppIcon
          name="clock"
          :size="16"
        />
        {{ dateLabel(reservation.travel_date) }} · {{ timeLabel(reservation.travel_time) }}
      </span>
      <span>
        <AppIcon
          name="user"
          :size="16"
        />
        {{ reservation.passengers }}
        {{ Number(reservation.passengers) === 1 ? 'pasajero' : 'pasajeros' }}
      </span>
    </div>
    <p
      v-if="reservation.notes"
      class="field-hint mt-4 whitespace-pre-wrap break-words"
    >
      {{ reservation.notes }}
    </p>
    <p
      v-if="reservation.status === 'pendiente'"
      class="pending-note"
    >
      Solicitud recibida. El viaje todavía no está confirmado.
    </p>
    <slot />
  </article>
</template>
