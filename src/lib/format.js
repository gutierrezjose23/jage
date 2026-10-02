export const services = {
  privado: 'Viaje privado',
  'huaral-lima': 'Huaral – Lima',
  aeropuerto: 'Traslado al aeropuerto',
}
export const statuses = ['pendiente', 'confirmada', 'cancelada', 'completada']
export const money = (value) =>
  new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(Number(value || 0))
export const dateLabel = (value) =>
  value
    ? new Intl.DateTimeFormat('es-PE', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        timeZone: 'America/Lima',
      }).format(new Date(value.includes('T') ? value : `${value.slice(0, 10)}T12:00:00-05:00`))
    : '—'
export const timeLabel = (value) => value?.slice(0, 5) || '—'
export const limaToday = () =>
  new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Lima',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
export const isFutureTrip = (date, time) =>
  new Date(`${date}T${time}:00-05:00`).getTime() > Date.now()
