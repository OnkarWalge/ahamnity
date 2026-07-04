import { CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react'

const RISK_CONFIG = {
  low: {
    icon: CheckCircle2,
    bg: 'bg-risk-low-bg',
    text: 'text-risk-low',
    ring: 'ring-risk-low/30',
  },
  medium: {
    icon: AlertTriangle,
    bg: 'bg-risk-medium-bg',
    text: 'text-risk-medium',
    ring: 'ring-risk-medium/30',
  },
  high: {
    icon: AlertOctagon,
    bg: 'bg-risk-high-bg',
    text: 'text-risk-high',
    ring: 'ring-risk-high/30',
  },
}

export default function RiskBadge({ level, label }) {
  const config = RISK_CONFIG[level] || RISK_CONFIG.medium
  const Icon = config.icon

  return (
    <div
      className={`
        inline-flex items-center gap-2.5 px-5 py-3 rounded-2xl ring-1
        ${config.bg} ${config.ring} animate-fadeUp
      `}
    >
      <Icon className={`w-6 h-6 ${config.text}`} strokeWidth={2} />
      <span className={`font-display font-semibold text-lg ${config.text}`}>{label}</span>
    </div>
  )
}