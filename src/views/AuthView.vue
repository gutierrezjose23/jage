<script setup>
import AppForm from '../components/AppForm.vue'
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, session, accountPath, loadSession } from '../lib/api.js'
import FormField from '../components/FormField.vue'
import AlertMessage from '../components/AlertMessage.vue'
import AppIcon from '../components/AppIcon.vue'
const route = useRoute()
const router = useRouter()
const register = computed(() => route.path === '/registro')
const form = reactive({
  first_name: '',
  last_name: '',
  phone: '',
  dni: '',
  email: '',
  password: '',
  confirm_password: '',
})
const busy = ref(false)
const error = ref('')
const fields = ref({})
watch(register, () => {
  error.value = ''
  fields.value = {}
  form.password = ''
  form.confirm_password = ''
})
async function submit() {
  if (busy.value) return
  error.value = ''
  fields.value = {}
  if (register.value && form.password !== form.confirm_password) {
    fields.value.confirm_password = 'Las contraseñas no coinciden.'
    error.value = 'Revisa la confirmación de tu contraseña.'
    return
  }
  busy.value = true
  try {
    await loadSession(true)
    const body = register.value
      ? {
          first_name: form.first_name.trim(),
          last_name: form.last_name.trim(),
          phone: form.phone.trim(),
          dni: form.dni.trim(),
          email: form.email.trim(),
          password: form.password,
        }
      : { email: form.email.trim(), password: form.password }
    const data = await api(`/auth/${register.value ? 'register' : 'login'}`, {
      method: 'POST',
      body,
    })
    session.user = data.user
    form.password = ''
    form.confirm_password = ''
    const next = route.query.siguiente
    await router.push(
      session.user.role === 'passenger' &&
        typeof next === 'string' &&
        /^\/(reservar|mis-reservas)(\?|$)/.test(next)
        ? next
        : accountPath(),
    )
  } catch (cause) {
    error.value = cause.message
    fields.value = cause.fields || {}
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <section class="auth-page page-shell">
    <div class="auth-story">
      <div
        class="auth-emblem"
        aria-hidden="true"
      >
        <AppIcon
          name="route"
          :size="30"
        />
      </div>
      <p class="eyebrow">TU ESPACIO JAGE</p>
      <h2>
        Un buen viaje
        <br />
        empieza aquí
        <span>.</span>
      </h2>
      <p>Organiza tus traslados y ten tus solicitudes siempre a mano.</p>
      <div class="auth-route">
        <AppIcon
          name="pin"
          :size="23"
        />
        <span>Huaral</span>
        <span class="route-line" />
        <AppIcon
          name="arrow"
          :size="28"
        />
        <span>Tu destino</span>
      </div>
      <p class="auth-story-bottom">
        <AppIcon
          name="car"
          :size="24"
        />
        VAMOS CONTIGO.
      </p>
    </div>
    <div class="auth-form-wrap">
      <p class="eyebrow muted">{{ register ? 'BIENVENIDO A BORDO' : 'QUÉ BUENO VERTE' }}</p>
      <h1>{{ register ? 'Crea tu cuenta.' : 'Inicia sesión.' }}</h1>
      <p class="muted mb-7">
        {{
          register
            ? 'Tus datos nos ayudan a coordinar tu viaje.'
            : 'Ingresa para continuar con tus viajes.'
        }}
      </p>
      <AlertMessage :message="error || session.error" />
      <AppForm
        class="form-stack"
        :disabled="busy"
        @submit="submit"
      >
        <div
          v-if="register"
          class="grid gap-5 sm:grid-cols-2"
        >
          <FormField
            label="Nombre"
            v-model="form.first_name"
            autocomplete="given-name"
            maxlength="80"
            :error="fields.first_name"
            required
          />
          <FormField
            label="Apellido"
            v-model="form.last_name"
            autocomplete="family-name"
            maxlength="80"
            :error="fields.last_name"
            required
          />
        </div>
        <FormField
          v-if="register"
          label="DNI"
          v-model="form.dni"
          inputmode="numeric"
          autocomplete="off"
          minlength="8"
          maxlength="8"
          pattern="[0-9]{8}"
          hint="Los 8 dígitos de tu documento."
          :error="fields.dni"
          required
        />
        <FormField
          v-if="register"
          label="Celular"
          v-model="form.phone"
          type="tel"
          inputmode="tel"
          autocomplete="tel"
          maxlength="20"
          pattern="[+0-9 \(\)\-]{7,20}"
          hint="Ejemplo: +51 934 613 286"
          :error="fields.phone"
          required
        />
        <FormField
          label="Correo electrónico"
          v-model="form.email"
          type="email"
          autocomplete="email"
          maxlength="254"
          :error="fields.email"
          required
        />
        <FormField
          label="Contraseña"
          v-model="form.password"
          type="password"
          :autocomplete="register ? 'new-password' : 'current-password'"
          :minlength="register ? 12 : undefined"
          maxlength="128"
          :hint="
            register
              ? 'Usa entre 12 y 128 caracteres. Puedes usar una frase larga y única.'
              : undefined
          "
          :error="fields.password"
          required
        />
        <FormField
          v-if="register"
          label="Repite tu contraseña"
          v-model="form.confirm_password"
          type="password"
          autocomplete="new-password"
          minlength="12"
          maxlength="128"
          :error="fields.confirm_password"
          required
        />
        <p
          v-if="register"
          class="field-hint"
        >
          Crearás una cuenta de cliente. Tus datos se usarán para gestionar tu cuenta y coordinar
          las solicitudes de viaje.
        </p>
        <button
          type="submit"
          class="btn btn-primary w-full"
          :disabled="busy"
        >
          {{ busy ? 'Un momento…' : register ? 'Crear mi cuenta' : 'Entrar a mi cuenta' }}
          <AppIcon name="next" />
        </button>
      </AppForm>
      <p class="auth-switch">
        {{ register ? '¿Ya tienes una cuenta?' : '¿Es tu primera vez aquí?' }}
        <RouterLink :to="{ path: register ? '/ingresar' : '/registro', query: route.query }">
          {{ register ? 'Inicia sesión' : 'Crea tu cuenta' }}
        </RouterLink>
      </p>
    </div>
  </section>
</template>
