// Centralised backend calls. Change BASE_URL here if the port/host changes.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9009'

/**
 * Runs the full pipeline: audio -> STT -> triage -> TTS -> case save.
 * @param {Blob} audioBlob - recorded audio from MediaRecorder
 * @param {string} language - language code (hi, mr, en, bn, te, ta)
 * @param {object} patientContext - optional { latitude, longitude, district }
 */
export async function runPipeline(audioBlob, language, patientContext = {}) {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.webm')
  form.append('language', language)

  if (patientContext.latitude != null) form.append('latitude', patientContext.latitude)
  if (patientContext.longitude != null) form.append('longitude', patientContext.longitude)
  if (patientContext.district) form.append('district', patientContext.district)

  const res = await fetch(`${BASE_URL}/api/pipeline/run`, {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}))
    throw new Error(errBody.detail || `Pipeline failed (${res.status})`)
  }

  return res.json()
}

/**
 * Finds nearby PHCs given GPS coordinates.
 */
export async function findNearbyPHCs(latitude, longitude, radiusKm = 15) {
  const params = new URLSearchParams({ lat: latitude, lng: longitude, radius_km: radiusKm })
  const res = await fetch(`${BASE_URL}/api/locator/nearby?${params}`)
  if (!res.ok) throw new Error(`Locator failed (${res.status})`)
  return res.json()
}

/**
 * Matches symptoms text to relevant government schemes.
 */
export async function matchSchemes(symptoms, language = 'hi', patientAge = null, patientGender = null) {
  const res = await fetch(`${BASE_URL}/api/schemes/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symptoms,
      language,
      patient_age: patientAge,
      patient_gender: patientGender,
    }),
  })
  if (!res.ok) throw new Error(`Scheme matching failed (${res.status})`)
  return res.json()
}

/**
 * Gets the browser's current GPS position as a Promise.
 * Resolves to null if permission denied or unavailable — caller should
 * handle gracefully (locator step is optional, not blocking).
 */
export function getCurrentLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null)
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
      () => resolve(null),
      { timeout: 8000 }
    )
  })
}

/**
 * Decodes a base64 MP3 string into a playable object URL.
 */
export function base64ToAudioUrl(base64) {
  const byteChars = atob(base64)
  const byteNumbers = new Array(byteChars.length)
  for (let i = 0; i < byteChars.length; i++) {
    byteNumbers[i] = byteChars.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  const blob = new Blob([byteArray], { type: 'audio/mpeg' })
  return URL.createObjectURL(blob)
}