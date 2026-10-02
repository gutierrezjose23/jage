import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { VApp, VForm, VTextField, VTextarea, VSelect } from 'vuetify/components'
import { es } from 'vuetify/locale'
import { aliases, mdi } from 'vuetify/iconsets/mdi-svg'

export default createVuetify({
  components: { VApp, VForm, VTextField, VTextarea, VSelect },
  icons: { defaultSet: 'mdi', aliases, sets: { mdi } },
  locale: { locale: 'es', messages: { es } },
  theme: {
    defaultTheme: 'jage',
    themes: {
      jage: {
        dark: false,
        colors: {
          primary: '#083bfa',
          secondary: '#6dd5e8',
          background: '#f5f7fb',
          surface: '#ffffff',
          'on-surface': '#17233f',
          error: '#a0392f',
          success: '#1b599c',
          'on-primary': '#ffffff',
          'on-secondary': '#17233f',
          'on-background': '#17233f',
          'surface-variant': '#eef3fc',
          'on-surface-variant': '#52617b',
          'on-error': '#ffffff',
          'on-success': '#ffffff',
        },
      },
    },
  },
  defaults: {
    VTextField: {
      variant: 'outlined',
      color: 'primary',
      rounded: 'lg',
      bgColor: 'surface',
      density: 'comfortable',
      hideDetails: 'auto',
    },
    VTextarea: {
      variant: 'outlined',
      color: 'primary',
      rounded: 'lg',
      bgColor: 'surface',
      density: 'comfortable',
      hideDetails: 'auto',
    },
    VSelect: {
      variant: 'outlined',
      color: 'primary',
      rounded: 'lg',
      bgColor: 'surface',
      density: 'comfortable',
      hideDetails: 'auto',
    },
  },
})
