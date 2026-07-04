import { Landmark, ArrowUpRight } from 'lucide-react'

export default function SchemeCard({ scheme, labels }) {
  return (
    <div className="bg-surface rounded-2xl shadow-card p-4 animate-fadeUp">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-saffron-soft flex items-center justify-center">
          <Landmark className="w-5 h-5 text-saffron" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-display font-semibold text-ink leading-snug">{scheme.name}</h3>
          <p className="text-sm text-ink-soft mt-1">{scheme.benefit}</p>
        </div>
      </div>

      {scheme.apply_url && (
        <a
          href={scheme.apply_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 mt-3 text-sm font-medium text-teal-bright"
        >
          {labels.learnMore}
          <ArrowUpRight className="w-3.5 h-3.5" />
        </a>
      )}
    </div>
  )
}