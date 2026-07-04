import { Mic, Square } from 'lucide-react'

/**
 * The signature element of Ahamnity. A breathing gradient orb at idle,
 * expanding waveform rings while recording. This is the one bold animated
 * moment in the whole app — everything else stays calm by design.
 */
export default function VoiceOrb({ isRecording, onPress, disabled }) {
  return (
    <div className="relative flex items-center justify-center w-48 h-48">
      {/* Expanding pulse rings — only while recording */}
      {isRecording && (
        <>
          <span className="absolute inset-0 rounded-full bg-saffron/40 animate-ringPulse" />
          <span
            className="absolute inset-0 rounded-full bg-saffron/40 animate-ringPulse"
            style={{ animationDelay: '0.5s' }}
          />
          <span
            className="absolute inset-0 rounded-full bg-saffron/40 animate-ringPulse"
            style={{ animationDelay: '1s' }}
          />
        </>
      )}

      <button
        onClick={onPress}
        disabled={disabled}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        className={`
          relative z-10 w-36 h-36 rounded-full flex items-center justify-center
          shadow-card-lg transition-transform duration-200
          active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed
          ${isRecording ? 'bg-saffron' : 'bg-gradient-to-br from-teal-deep to-teal-bright animate-breathe'}
        `}
      >
        {isRecording ? (
          <Square className="w-12 h-12 text-white" fill="white" />
        ) : (
          <Mic className="w-14 h-14 text-white" strokeWidth={1.75} />
        )}
      </button>
    </div>
  )
}