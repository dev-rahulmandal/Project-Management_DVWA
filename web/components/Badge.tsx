// Shared presentational badge (used by project header + task rows).
export function Badge({ text, tone }: { text: string; tone: 'green' | 'slate' | 'amber' | 'red' }) {
  const tones = {
    green: 'bg-green-50 text-green-700',
    slate: 'bg-slate-100 text-slate-500',
    amber: 'bg-amber-50 text-amber-700',
    red: 'bg-red-50 text-red-700',
  }
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${tones[tone]}`}>
      {text}
    </span>
  )
}
