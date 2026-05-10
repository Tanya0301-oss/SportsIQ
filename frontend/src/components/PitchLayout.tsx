import type { Player } from '../api/client'
import styles from './PitchLayout.module.css'

interface Props { players: Player[] }

const POS_ORDER = ['GK', 'DEF', 'MID', 'FWD']

function PlayerToken({ player }: { player: Player }) {
  const initials = player.name.split(' ').map(w => w[0]).join('').slice(0, 2)
  const colors: Record<string, string> = {
    GK: '#f59e0b', DEF: '#06b6d4', MID: '#6c63ff', FWD: '#ef4444'
  }
  const color = colors[player.position] ?? '#6c63ff'
  return (
    <div className={styles.token} title={`${player.name} (£${player.salary}m | ${player.expected_points}pts)`}>
      <div className={styles.circle} style={{ borderColor: color, boxShadow: `0 0 12px ${color}55` }}>
        <span className={styles.initials}>{initials}</span>
      </div>
      <span className={styles.name}>{player.name.split(' ').slice(-1)[0]}</span>
      <span className={styles.pts} style={{ color }}>{player.expected_points.toFixed(1)}</span>
    </div>
  )
}

export default function PitchLayout({ players }: Props) {
  const byPos: Record<string, Player[]> = { GK: [], DEF: [], MID: [], FWD: [] }
  players.forEach(p => { (byPos[p.position] ??= []).push(p) })

  return (
    <div className={styles.pitch}>
      <div className={styles.pitchLines}>
        <div className={styles.centerCircle} />
        <div className={styles.centerLine} />
        <div className={styles.penaltyTop} />
        <div className={styles.penaltyBottom} />
      </div>
      <div className={styles.field}>
        {POS_ORDER.map(pos => (
          <div key={pos} className={styles.row}>
            {(byPos[pos] ?? []).map(p => <PlayerToken key={p.id} player={p} />)}
          </div>
        ))}
      </div>
    </div>
  )
}
