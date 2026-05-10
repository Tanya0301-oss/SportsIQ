import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine
} from 'recharts'

interface DataPoint {
  minute: number
  home: number
  draw: number
  away: number
}

interface Props {
  data: DataPoint[]
  homeTeam: string
  awayTeam: string
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--color-bg-2)',
      border: '1px solid var(--color-border)',
      borderRadius: 10,
      padding: '10px 14px',
      fontSize: 12,
    }}>
      <p style={{ color: 'var(--color-text-2)', marginBottom: 6 }}>Minute {label}'</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {(p.value * 100).toFixed(1)}%
        </p>
      ))}
    </div>
  )
}

export default function ProbabilityChart({ data, homeTeam, awayTeam }: Props) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="minute"
          tick={{ fill: 'var(--color-text-3)', fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: 'var(--color-border)' }}
          label={{ value: "min", position: 'insideRight', fill: 'var(--color-text-3)', fontSize: 10 }}
        />
        <YAxis
          tickFormatter={v => `${(v * 100).toFixed(0)}%`}
          domain={[0, 1]}
          tick={{ fill: 'var(--color-text-3)', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <ReferenceLine y={0.333} stroke="rgba(255,255,255,0.06)" strokeDasharray="4 4" />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8, color: 'var(--color-text-2)' }}
          formatter={(v) => v === 'home' ? homeTeam : v === 'away' ? awayTeam : 'Draw'}
        />
        <Line
          type="monotone" dataKey="home" stroke="var(--color-green)"
          strokeWidth={2.5} dot={false} name="home"
          strokeShadowColor="rgba(34,197,94,0.4)"
        />
        <Line
          type="monotone" dataKey="draw" stroke="var(--color-amber)"
          strokeWidth={2} dot={false} name="draw" strokeDasharray="5 3"
        />
        <Line
          type="monotone" dataKey="away" stroke="var(--color-red)"
          strokeWidth={2.5} dot={false} name="away"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
