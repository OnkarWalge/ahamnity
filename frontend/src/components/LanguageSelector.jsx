import { LANGUAGES } from '../i18n'

export default function LanguageSelector({ selected, onSelect }) {
  return (
    <div className="flex gap-1.5 overflow-x-auto" role="group" aria-label="Select language">
      {LANGUAGES.map((lang) => (
        <button
          key={lang.code}
          onClick={() => onSelect(lang.code)}
          aria-pressed={selected === lang.code}
          className={`
            px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap
            transition-colors duration-150
            ${
              selected === lang.code
                ? 'bg-teal-deep text-white'
                : 'bg-surface text-ink-soft border border-ink-soft/15 hover:border-teal-bright/40'
            }
          `}
        >
          {lang.label}
        </button>
      ))}
    </div>
  )
}