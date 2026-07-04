import { Phone, MapPin, Building2 } from 'lucide-react'

export default function PHCCard({ phc, labels }) {
  return (
    <div className="bg-surface rounded-2xl shadow-card p-4 animate-fadeUp">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-teal-bright/10 flex items-center justify-center">
          <Building2 className="w-5 h-5 text-teal-bright" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-display font-semibold text-ink leading-snug">{phc.name}</h3>
          <p className="text-sm text-ink-soft mt-0.5">{phc.address}</p>
          <p className="text-sm font-medium text-teal-bright mt-1">{phc.distance_km} km</p>
        </div>
      </div>

      <div className="flex gap-2 mt-3">
        {phc.phone && (
          <a
            href={`tel:${phc.phone}`}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-teal-deep text-white text-sm font-medium active:scale-95 transition-transform"
          >
            <Phone className="w-4 h-4" />
            {labels.call}
          </a>
        )}
        <a
          href={phc.maps_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-bg border border-ink-soft/15 text-ink text-sm font-medium active:scale-95 transition-transform"
        >
          <MapPin className="w-4 h-4" />
          {labels.viewMap}
        </a>
      </div>
    </div>
  )
}