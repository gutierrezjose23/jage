import { test, expect } from '@playwright/test'

const password = process.env.JAGE_E2E_PASSWORD

async function login(page, email) {
  await page.goto('/ingresar')
  await page.getByLabel(/Correo\ electrónico/).fill(email)
  await page.getByLabel(/Contraseña/).fill(password)
  await page.getByRole('button', { name: 'Entrar a mi cuenta' }).click()
}

async function selectOption(page, combobox, name) {
  // The selected VSelect input is transparent; users click its visible field wrapper.
  await combobox.locator('..').click()
  await expect(combobox).toHaveAttribute('aria-expanded', 'true')
  // Vuetify renders its accessible listbox in an overlay outside the form/card.
  await page.getByRole('option', { name, exact: typeof name === 'string' }).click()
  await expect(combobox).toHaveAttribute('aria-expanded', 'false')
}

async function captureMobile(page, name) {
  const previousViewport = page.viewportSize()
  await page.setViewportSize({ width: 360, height: 800 })
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      ),
    )
    .toBe(true)
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }))
  await page.screenshot({ path: `.test-artifacts/${name}-mobile.png`, fullPage: true })
  await page.setViewportSize(previousViewport)
}

function submissionsTo(page, pathname) {
  const submissions = []
  page.on('request', (request) => {
    if (request.method() === 'POST' && new URL(request.url()).pathname === pathname) {
      submissions.push(request.postDataJSON())
    }
  })
  return submissions
}

for (const width of [360, 768, 900, 1440]) {
  test(`inicio accesible y recursos válidos a ${width}px`, async ({ page }) => {
    const failures = []
    page.on('pageerror', (error) => failures.push(error.message))
    page.on('response', (response) => {
      if (response.status() >= 400) failures.push(`${response.status()} ${response.url()}`)
    })
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Tu próximo')
    await expect(page.locator('#servicios')).toBeVisible()
    await expect(page.locator('#como-reservar')).toBeVisible()
    await expect(page.locator('#contacto')).toBeVisible()
    const metrics = await page.evaluate(() => ({
      width: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
      inputs: [...document.querySelectorAll('input, textarea, select')]
        .filter((el) => el.checkVisibility() && el.getAttribute('aria-hidden') !== 'true')
        .map((el) => ({
          font: parseFloat(getComputedStyle(el).fontSize),
          labelled: !!document.querySelector(`label[for="${el.id}"]`),
        })),
      images: [...document.images].every((img) => img.complete && img.naturalWidth > 0),
    }))
    expect(metrics.scroll).toBeLessThanOrEqual(metrics.width)
    expect(metrics.images).toBe(true)
    expect(metrics.inputs.every((item) => item.font >= 16 && item.labelled)).toBe(true)
    if (width <= 980) {
      await page.getByRole('button', { name: 'Abrir menú' }).click()
      await expect(page.getByRole('navigation', { name: 'Navegación móvil' })).toBeVisible()
      await page
        .getByRole('navigation', { name: 'Navegación móvil' })
        .getByRole('link', { name: 'Iniciar sesión' })
        .click()
      await expect(page).toHaveURL(/\/ingresar$/)
      await expect(page.getByLabel(/Contraseña/)).toBeVisible()
    }
    expect(failures).toEqual([])
    await page.goto('/')
    await page.screenshot({ path: `.test-artifacts/home-${width}.png`, fullPage: true })
    await page.screenshot({ path: `.test-artifacts/home-${width}-viewport.png` })
  })
}

test('contacto prepara datos correctos y ubicación requiere una acción explícita', async ({
  page,
}) => {
  await page.addInitScript(() => {
    window.locationCalls = 0
    Object.defineProperty(navigator, 'geolocation', {
      value: {
        getCurrentPosition(success) {
          window.locationCalls++
          success({ coords: { latitude: -11.495, longitude: -77.207, accuracy: 20 } })
        },
      },
    })
  })
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  expect(await page.evaluate(() => window.locationCalls)).toBe(0)
  await page.getByRole('button', { name: 'Preparar mensaje' }).click()
  await expect(page.getByLabel(/Tu\ nombre/)).toHaveAccessibleDescription(/Completa este campo/)
  await expect(page.getByRole('link', { name: 'Abrir WhatsApp' })).toHaveCount(0)
  await page.getByLabel(/Tu\ nombre/).fill('Ana García')
  await page.getByLabel(/Correo\ electrónico/).fill('ana@example.test')
  await page.getByLabel(/¿En\ qué\ podemos\ ayudarte\?/).fill('Necesito un traslado al aeropuerto.')
  await page.getByRole('button', { name: 'Usar mi ubicación actual' }).click()
  await expect(page.getByText('Revisa tu punto de partida')).toBeVisible()
  await expect(page.getByLabel('Punto de partida (opcional)')).toHaveValue('')
  await page.getByRole('button', { name: 'Usar este origen' }).click()
  await expect(page.getByLabel('Punto de partida (opcional)')).toHaveValue(/google.com\/maps/)
  await page.getByRole('button', { name: 'Preparar mensaje' }).click()
  const link = page.getByRole('link', { name: 'Abrir WhatsApp' })
  await expect(link).toBeVisible()
  const url = new URL(await link.getAttribute('href'))
  expect(url.pathname).toBe('/51934613286')
  expect(url.searchParams.get('text')).toContain('Ana García')
  expect(url.searchParams.get('text')).toContain('ana@example.test')
  expect(url.searchParams.get('text')).toContain('google.com/maps')
  await page.getByLabel(/Tu\ nombre/).fill('Beatriz')
  await expect(link).toHaveCount(0)
})

for (const [code, expected] of [
  [1, 'No se autorizó'],
  [2, 'No pudimos encontrar'],
  [3, 'tardó demasiado'],
]) {
  test(`geolocalización maneja el error ${code}`, async ({ page }) => {
    await page.addInitScript((errorCode) => {
      Object.defineProperty(navigator, 'geolocation', {
        value: {
          getCurrentPosition(success, failure) {
            failure({ code: errorCode })
          },
        },
      })
    }, code)
    await page.goto('/')
    await page.getByRole('button', { name: 'Usar mi ubicación actual' }).click()
    await expect(page.getByRole('alert')).toContainText(expected)
    await page.getByLabel('Punto de partida (opcional)').fill('Plaza de Huaral')
    await expect(page.getByLabel('Punto de partida (opcional)')).toHaveValue('Plaza de Huaral')
  })
}

test('ingreso valida los campos y permite corregirlos antes de enviar', async ({ page }) => {
  const attempts = submissionsTo(page, '/api/auth/login')
  await page.goto('/ingresar')
  await page.screenshot({ path: '.test-artifacts/login-desktop.png', fullPage: true })
  await captureMobile(page, 'login')
  const email = page.getByLabel(/Correo\ electrónico/)
  const submit = page.getByRole('button', { name: 'Entrar a mi cuenta' })
  await submit.click()
  await expect(email).toHaveAccessibleDescription(/Completa este campo/)
  expect(attempts).toHaveLength(0)
  await email.fill('correo-invalido')
  await page.getByLabel(/Contraseña/).fill(password)
  await submit.click()
  await expect(email).toHaveAccessibleDescription(/correo válido/)
  expect(attempts).toHaveLength(0)
  await email.fill('admin@example.test')
  await submit.click()
  await expect(page).toHaveURL(/administracion/)
  expect(attempts).toHaveLength(1)
})

test('cliente se registra, solicita, consulta y cierra sesión sin recargas', async ({ page }) => {
  test.setTimeout(60000)
  const email = `cliente-${Date.now()}@example.test`
  const registrations = submissionsTo(page, '/api/auth/register')
  const bookings = submissionsTo(page, '/api/reservations')
  let documents = 0
  page.on('request', (request) => {
    if (request.resourceType() === 'document') documents++
  })
  await page.goto('/registro')
  await captureMobile(page, 'register')
  await page.getByRole('button', { name: 'Crear mi cuenta' }).click()
  await expect(page.getByLabel(/Nombre/)).toHaveAccessibleDescription(/Completa este campo/)
  expect(registrations).toHaveLength(0)
  await page.getByLabel(/Nombre/).fill('María')
  await page.getByLabel(/Apellido/).fill('Pérez')
  await page.getByLabel('DNI', { exact: true }).fill('01234567')
  await page.getByLabel(/Celular/).fill('934613286')
  await page.getByLabel(/Correo\ electrónico/).fill(email)
  await page.getByLabel(/Contraseña/).fill('corta')
  await page.getByLabel(/Repite\ tu\ contraseña/).fill(password)
  await page.getByRole('button', { name: 'Crear mi cuenta' }).click()
  await expect(page.getByLabel(/Contraseña/)).toHaveAccessibleDescription(/al menos 12 caracteres/)
  expect(registrations).toHaveLength(0)
  await page.getByLabel(/Contraseña/).fill(password)
  await page.getByLabel(/Repite\ tu\ contraseña/).fill(`${password}-distinta`)
  await page.getByRole('button', { name: 'Crear mi cuenta' }).click()
  await expect(page.getByText('Las contraseñas no coinciden.')).toBeVisible()
  expect(registrations).toHaveLength(0)
  await page.getByLabel(/Repite\ tu\ contraseña/).fill(password)
  await page.getByRole('button', { name: 'Crear mi cuenta' }).click()
  await expect(page).toHaveURL(/mis-reservas/)
  expect(registrations).toHaveLength(1)
  await page.getByRole('link', { name: 'Nueva reserva', exact: true }).click()
  await expect(page).toHaveURL(/\/reservar$/)
  await captureMobile(page, 'booking')
  const bookingSubmit = page.getByRole('button', { name: 'Enviar solicitud de reserva' })
  await bookingSubmit.click()
  const service = page.getByRole('combobox', { name: /Servicio/ })
  await expect(service).toHaveAccessibleDescription(/Completa este campo/)
  expect(bookings).toHaveLength(0)
  await service.focus()
  await service.press('ArrowDown')
  await expect(page.getByRole('option', { name: 'Traslado al aeropuerto' })).toBeVisible()
  await expect(page.getByRole('option', { name: 'Viaje privado', exact: true })).toBeFocused()
  await page.keyboard.press('End')
  await expect(page.getByRole('option', { name: 'Traslado al aeropuerto' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(service).toHaveAttribute('aria-expanded', 'false')
  await expect(service).toHaveValue('Traslado al aeropuerto')
  await page.getByLabel(/Origen/).fill('Plaza de Armas de Huaral')
  await page.getByLabel(/Destino/).fill('Aeropuerto Jorge Chávez')
  const future = new Date(Date.now() + 2 * 86400000).toISOString().slice(0, 10)
  await page.getByLabel(/Fecha\ de\ viaje/).fill(future)
  await page.getByLabel(/Hora\ de\ salida/).fill('10:30')
  const passengers = page.getByLabel(/Número\ de\ pasajeros/)
  await passengers.fill('9')
  await bookingSubmit.click()
  await expect(passengers).toHaveAccessibleDescription(/máximo es 8/)
  expect(bookings).toHaveLength(0)
  await passengers.fill('1.5')
  await bookingSubmit.click()
  await expect(passengers).toHaveAccessibleDescription(/incrementos de 1/)
  expect(bookings).toHaveLength(0)
  await passengers.fill('2')
  await bookingSubmit.click()
  await expect(page).toHaveURL(/mis-reservas/)
  expect(bookings).toHaveLength(1)
  expect(bookings[0]).toMatchObject({ service: 'aeropuerto', passengers: 2 })
  await expect(page.locator('.status-badge')).toHaveText(/pendiente/i)
  await expect(page.getByText('Aeropuerto Jorge Chávez', { exact: true })).toBeVisible()
  expect(documents).toBe(1)
  await page.getByRole('button', { name: 'Salir', exact: true }).click()
  await expect(page).toHaveURL(/\/$/)
  await login(page, email)
  await expect(page).toHaveURL(/mis-reservas/)
  await expect(page.getByText('Aeropuerto Jorge Chávez', { exact: true })).toBeVisible()
})

test('roles abren sus paneles reales y las rutas directas funcionan', async ({ page }) => {
  await login(page, 'admin@example.test')
  await expect(page).toHaveURL(/administracion/)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Solicitudes de viaje' })).toBeVisible()
  await page.screenshot({ path: '.test-artifacts/admin-desktop.png', fullPage: true })
  await captureMobile(page, 'admin')
  await page.getByRole('button', { name: 'Salir', exact: true }).click()
  await expect(page).toHaveURL(/\/$/)
  await login(page, 'driver@example.test')
  await expect(page).toHaveURL(/conductor/)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.locator('.wallet-amount')).toBeVisible()
  await page.setViewportSize({ width: 360, height: 800 })
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  )
  expect(overflow).toBe(false)
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }))
  await page.screenshot({ path: '.test-artifacts/driver-mobile.png', fullPage: true })
})

test('administración crea conductor, registra saldo y promoción, y descuenta la comisión al completar', async ({
  page,
  browser,
}) => {
  const suffix = String(Date.now())
  const driverName = `Luis${suffix}`
  const driverEmail = `conductor-${suffix}@example.test`
  const origin = `Huaral prueba ${suffix}`
  const setup = await browser.newContext({ baseURL: 'http://127.0.0.1:5010' })
  const session = await (await setup.request.get('/api/session')).json()
  const registration = await setup.request.post('/api/auth/register', {
    headers: { 'X-CSRFToken': session.csrf_token },
    data: {
      first_name: 'Cliente',
      last_name: 'Integración',
      phone: '934613286',
      dni: '07654321',
      email: `setup-${suffix}@example.test`,
      password,
    },
  })
  expect(registration.status()).toBe(201)
  const auth = await registration.json()
  const booking = await setup.request.post('/api/reservations', {
    headers: { 'X-CSRFToken': auth.csrf_token },
    data: {
      service: 'privado',
      origin,
      destination: 'Lima',
      travel_date: new Date(Date.now() + 2 * 86400000).toISOString().slice(0, 10),
      travel_time: '11:00',
      passengers: 1,
      notes: '',
    },
  })
  expect(booking.status()).toBe(201)
  await setup.close()

  await login(page, 'admin@example.test')
  await page.getByRole('button', { name: 'Conductores y saldo', exact: true }).click()
  await page.getByRole('button', { name: 'Crear conductor', exact: true }).click()
  await captureMobile(page, 'admin-driver-form')
  await page.getByLabel(/Nombre/).fill(driverName)
  await page.getByLabel(/Apellido/).fill('Prueba')
  await page.getByLabel('DNI', { exact: true }).fill('02345678')
  await page.getByLabel('Placa del carro').fill('abc123')
  await page.getByLabel(/Celular/).fill('934613286')
  await page.getByLabel(/Correo/).fill(driverEmail)
  await page.getByLabel(/Contraseña inicial/).fill(password)
  await page.getByRole('button', { name: 'Crear cuenta de conductor' }).click()
  const driver = page.locator('.driver-card').filter({ hasText: driverEmail })
  await expect(driver).toBeVisible()
  await expect(driver).toContainText('02345678')
  await expect(driver).toContainText('ABC-123')
  await driver.getByRole('button', { name: 'Ajustar saldo' }).click()
  await page.getByLabel(/Importe del ajuste/).fill('40.00')
  await page.getByLabel(/Motivo o referencia/).fill('Abono de prueba verificado fuera de la app')
  await page.getByRole('button', { name: 'Registrar ajuste' }).click()
  await expect(driver.locator('.driver-balance strong')).toContainText('40.00')

  await page.getByRole('button', { name: 'Promociones', exact: true }).click()
  await page.getByRole('button', { name: 'Crear promoción', exact: true }).click()
  await page.getByLabel(/Nombre de la promoción/).fill(`Bono ${suffix}`)
  await page
    .getByLabel(/Descripción y condiciones/)
    .fill('Beneficio de prueba para comisión de viajes')
  await page.getByLabel(/Bono de saldo/).fill('5.50')
  await page
    .getByLabel(/Fecha de vencimiento/)
    .fill(new Date(Date.now() + 2 * 86400000).toISOString().slice(0, 10))
  await page.getByRole('button', { name: 'Publicar promoción' }).click()
  await expect(page.getByRole('heading', { name: `Bono ${suffix}` })).toBeVisible()

  await page.getByRole('button', { name: 'Reservas', exact: true }).click()
  const card = page.locator('.reservation-card').filter({ hasText: origin })
  await card.getByRole('button', { name: 'Gestionar reserva' }).click()
  await selectOption(page, card.getByRole('combobox', { name: /Estado/ }), 'confirmada')
  await selectOption(
    page,
    card.getByRole('combobox', { name: /Asignar conductor/ }),
    new RegExp(driverName),
  )
  await card.getByLabel(/Comisión de este viaje/).fill('7.50')
  await card.getByRole('button', { name: 'Guardar cambios' }).click()
  await expect(card.locator('.status-badge')).toHaveText(/confirmada/i)
  await card.getByRole('button', { name: 'Gestionar reserva' }).click()
  await selectOption(page, card.getByRole('combobox', { name: /Estado/ }), 'completada')
  await card.getByRole('button', { name: 'Guardar cambios' }).click()
  await expect(card.locator('.status-badge')).toHaveText(/completada/i)
  await expect(card.getByRole('button', { name: 'Gestionar reserva' })).toHaveCount(0)
  await page.getByRole('button', { name: 'Salir', exact: true }).click()
  await expect(page).toHaveURL(/\/$/)

  await login(page, driverEmail)
  await expect(page.locator('.wallet-amount')).toContainText('32.50')
  await expect(page.getByText(origin, { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Promociones', exact: true }).click()
  const promotion = page.locator('.promo-card').filter({ hasText: `Bono ${suffix}` })
  await promotion.getByRole('button', { name: 'Canjear bono' }).click()
  await expect(page.locator('.wallet-amount')).toContainText('38.00')
  await expect(promotion.getByRole('button', { name: 'Bono canjeado' })).toBeDisabled()
  await page.getByRole('button', { name: 'Historial de saldo', exact: true }).click()
  await expect(page.locator('.ledger-row')).toHaveCount(3)
  await page.setViewportSize({ width: 360, height: 800 })
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true)
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }))
  await page.screenshot({ path: '.test-artifacts/driver-ledger-mobile.png', fullPage: true })
})
