import { useState, useRef } from 'react'
import VoiceOrb from './components/VoiceOrb'
import LanguageSelector from './components/LanguageSelector'
import RiskBadge from './components/RiskBadge'
import AudioPlayer from './components/AudioPlayer'
import PHCCard from './components/PHCCard'
import SchemeCard from './components/SchemeCard'
import { runPipeline, findNearbyPHCs, matchSchemes, getCurrentLocation, base64ToAudioUrl } from './api'
import { t } from './i18n'
import { ChevronLeft, RotateCcw, AlertCircle } from 'lucide-react'

// idle -> recording -> processing -> results
//                                  -> error

export default function App() {
  const [screen, setScreen] = useState('idle')
  const [language, setLanguage] = useState('hi')
  const [result, setResult] = useState(null)
  const [phcs, setPhcs] = useState([])
  const [schemes, setSchemes] = useState([])
  const [extrasLoading, setExtrasLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const L = (key) => t(language, key)

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        processRecording(blob)
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setScreen('recording')
    } catch (e) {
      setErrorMsg(L('micPermission'))
      setScreen('error')
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
      setScreen('processing')
    }
  }

  function handleOrbPress() {
    if (screen === 'idle') startRecording()
    else if (screen === 'recording') stopRecording()
  }

  async function processRecording(blob) {
    try {
      const data = await runPipeline(blob, language)
      setResult(data)
      setScreen('results')
      loadExtras(data)
    } catch (e) {
      setErrorMsg(e.message || 'Something went wrong')
      setScreen('error')
    }
  }

  async function loadExtras(pipelineResult) {
    setExtrasLoading(true)
    try {
      const [location, schemeData] = await Promise.all([
        getCurrentLocation(),
        matchSchemes(pipelineResult.transcription, pipelineResult.detected_language),
      ])

      setSchemes(schemeData.matched_schemes || [])

      if (location) {
        const phcData = await findNearbyPHCs(location.latitude, location.longitude)
        setPhcs(phcData.phcs || [])
      }
    } catch (e) {
      // Non-blocking — patient already has their triage result regardless
      console.error('Extras failed:', e)
    } finally {
      setExtrasLoading(false)
    }
  }

  function reset() {
    setResult(null)
    setPhcs([])
    setSchemes([])
    setErrorMsg('')
    setScreen('idle')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="px-5 pt-6 pb-3 flex items-center justify-between max-w-md mx-auto w-full">
        <h1 className="font-display font-bold text-xl text-teal-bright">Ahamnity</h1>
        {screen !== 'results' && (
          <LanguageSelector selected={language} onSelect={setLanguage} />
        )}
        {screen === 'results' && (
          <button onClick={reset} aria-label={L('back')} className="p-2 -mr-2">
            <ChevronLeft className="w-6 h-6 text-ink-soft" />
          </button>
        )}
      </header>

      <main className="flex-1 max-w-md mx-auto w-full px-5 pb-8">
        {(screen === 'idle' || screen === 'recording') && (
          <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
            <p className="font-display text-base text-ink-soft mb-10">{L('tagline')}</p>

            <VoiceOrb isRecording={screen === 'recording'} onPress={handleOrbPress} />

            <p className="mt-8 font-medium text-ink">
              {screen === 'recording' ? L('recording') : L('tapToSpeak')}
            </p>
          </div>
        )}

        {screen === 'processing' && (
          <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
            <div className="w-16 h-16 rounded-full border-4 border-teal-bright/20 border-t-teal-bright animate-spin" />
            <p className="mt-6 font-medium text-ink">{L('processing')}</p>
          </div>
        )}

        {screen === 'error' && (
          <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
            <AlertCircle className="w-12 h-12 text-risk-high mb-4" />
            <p className="text-ink mb-6">{errorMsg}</p>
            <button
              onClick={reset}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-deep text-white font-medium"
            >
              <RotateCcw className="w-4 h-4" />
              {L('tryAgain')}
            </button>
          </div>
        )}

        {screen === 'results' && result && (
          <div className="space-y-5 pt-2">
            <RiskBadge level={result.risk_level} label={L(`risk${capitalize(result.risk_level)}`)} />

            <div className="bg-surface rounded-2xl shadow-card p-5 animate-fadeUp">
              <p className="text-ink leading-relaxed">{result.advice}</p>
            </div>

            {result.audio_base64 && (
              <AudioPlayer
                audioUrl={base64ToAudioUrl(result.audio_base64)}
                playLabel={L('playAdvice')}
                pauseLabel={L('pauseAdvice')}
              />
            )}

            {extrasLoading && (
              <p className="text-sm text-ink-soft text-center py-2">{L('findingHelp')}</p>
            )}

            {phcs.length > 0 && (
              <section>
                <h2 className="font-display font-semibold text-ink mb-3">{L('nearbyHeading')}</h2>
                <div className="space-y-3">
                  {phcs.slice(0, 3).map((phc) => (
                    <PHCCard key={phc.place_id} phc={phc} labels={{ call: L('call'), viewMap: L('viewMap') }} />
                  ))}
                </div>
              </section>
            )}

            {schemes.length > 0 && (
              <section>
                <h2 className="font-display font-semibold text-ink mb-3">{L('schemesHeading')}</h2>
                <div className="space-y-3">
                  {schemes.map((scheme) => (
                    <SchemeCard key={scheme.id} scheme={scheme} labels={{ learnMore: L('learnMore') }} />
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </main>

      {/* Persistent disclaimer — only on idle/recording, results already includes it in advice text */}
      {(screen === 'idle' || screen === 'recording') && (
        <footer className="px-5 pb-6 text-center max-w-md mx-auto w-full">
          <p className="text-xs text-ink-soft/70">{L('disclaimer')}</p>
        </footer>
      )}
    </div>
  )
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s
}