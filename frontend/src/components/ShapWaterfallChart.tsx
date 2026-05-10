import { BarChart, Bar, XAxis, YAxis, Cell, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import type { ShapFeature } from '../api/client'

interface Props { features: ShapFeature[]; homeTeam: string }

const LABELS: Record<string, string> = {
  goal_diff: 'Goal Diff', home_goals: 'Home Goals', away_goals: 'Away Goals',
  home_red: 'Home Reds', away_red: 'Away Reds', shots_home: 'Home Shots',
  shots_away: 'Away Shots', possession_home: 'Possession', time_remaining_frac: 'Time Left',
  is_tied: 'Tied', home_form_5: 'Home Form', away_form_5: 'Away Form', minute: 'Minute',
}

function Tip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{ background: 'var(--color-bg-2)', border: '1px solid var(--color-border)', borderRadius: 10, padding: '10px 14px', fontSize: 12 }}>
      <p style={{ fontWeight: 600, marginBottom: 4 }}>{LABELS[d.feature] ?? d.feature}</p>
      <p style={{ color: 'var(--color-text-2)' }}>Value: <b>{d.raw_value}</b></p>
      <p style={{ color: d.shap_value >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}>
        Impact: <b>{d.shap_value >= 0 ? '+' : ''}{(d.shap_value * 100).toFixed(1)}%</b>
      </p>
    </div>
  )
}

export default function ShapWaterfallChart({ features }: Props) {
  const top = features.slice(0, 8).sort((a, b) => a.shap_value - b.shap_value)
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={top} layout="vertical" margin={{ top: 0, right: 20, left: 100, bottom: 0 }}>
        <XAxis type="number" tickFormatter={v => `${(v*100).toFixed(0)}%`} tick={{ fill: 'var(--color-text-3)', fontSize: 11 }} tickLine={false} axisLine={false} domain={['auto','auto']} />
        <YAxis type="category" dataKey="feature" tickFormatter={(v: string) => LABELS[v] ?? v} tick={{ fill: 'var(--color-text-2)', fontSize: 11 }} tickLine={false} axisLine={false} width={95} />
        <ReferenceLine x={0} stroke="rgba(255,255,255,0.15)" />
        <Tooltip content={<Tip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
        <Bar dataKey="shap_value" radius={[0, 4, 4, 0]}>
          {top.map((e, i) => <Cell key={i} fill={e.shap_value >= 0 ? 'var(--color-green)' : 'var(--color-red)'} fillOpacity={0.85} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
