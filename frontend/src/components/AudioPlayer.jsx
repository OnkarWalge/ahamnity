import { useRef, useState } from 'react'
import { Play, Pause, Volume2 } from 'lucide-react'

export default function AudioPlayer({ audioUrl, playLabel, pauseLabel }) {
  const audioRef = useRef(null)
  const [isPlaying, setIsPlaying] = useState(false)

  const toggle = () => {
    if (!audioRef.current) return
    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play()
    }
    setIsPlaying(!isPlaying)
  }

  return (
    <div className="flex items-center gap-3 bg-surface rounded-2xl shadow-card p-4">
      <button
        onClick={toggle}
        aria-label={isPlaying ? pauseLabel : playLabel}
        className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-teal-deep to-teal-bright flex items-center justify-center active:scale-95 transition-transform"
      >
        {isPlaying ? (
          <Pause className="w-5 h-5 text-white" fill="white" />
        ) : (
          <Play className="w-5 h-5 text-white" fill="white" />
        )}
      </button>

      <div className="flex items-center gap-2 text-ink-soft">
        <Volume2 className="w-4 h-4" />
        <span className="text-sm font-medium">{isPlaying ? pauseLabel : playLabel}</span>
      </div>

      <audio
        ref={audioRef}
        src={audioUrl}
        onEnded={() => setIsPlaying(false)}
        className="hidden"
      />
    </div>
  )
}