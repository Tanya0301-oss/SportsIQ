import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, type Player, type LineupResponse } from '../api/client'
import PitchLayout from '../components/PitchLayout'
import styles from './LineupOptimizer.module.css'

export default function LineupOptimizer() {
  const [budget, setBudget] = useState(100)
  const [formation, setFormation] = useState('4-3-3')
  const [result, setResult] = useState<LineupResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { data: players } = useQuery({ queryKey: ['players'], queryFn: api.getPlayers })

  async function handleOptimize() {
    if (!players?.length) return
    setLoading(true); setError('')
    try {
      const res = await api.optimizeLineup({ budget, formation, players })
      setResult(res)
    } catch (e: any) {
      setError(e.message ?? 'Optimisation failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="page">
      <div className="container">
        <div className={styles.hero}>
          <h1 className={styles.title}>Fantasy Lineup <span className={styles.accent}>Optimizer</span></h1>
          <p className={styles.sub}>Integer linear programming finds the mathematically optimal squad within your budget.</p>
        </div>

        <div className={styles.layout}>
          {/* Controls */}
          <div className={`card ${styles.controls}`}>
            <h2 className={styles.panelTitle}>Constraints</h2>

            <div className={styles.field}>
              <label className="label">Budget (£m)</label>
              <input id="budget" type="number" className="input" value={budget}
                onChange={e => setBudget(Number(e.target.value))} min={50} max={200} step={5} />
            </div>

            <div className={styles.field}>
              <label className="label">Formation</label>
              <select id="formation" className="input" value={formation} onChange={e => setFormation(e.target.value)}>
                <option value="4-3-3">4-3-3</option>
                <option value="4-4-2">4-4-2</option>
                <option value="3-5-2">3-5-2</option>
                <option value="flexible">Flexible</option>
              </select>
            </div>

            <div className={styles.field}>
              <label className="label">Player Pool</label>
              <p className={styles.poolInfo}>{players?.length ?? 0} players available</p>
            </div>

            <button className={`btn btn-primary ${styles.optimizeBtn}`} onClick={handleOptimize} disabled={loading || !players?.length}>
              {loading ? 'Solving…' : '⚡ Optimise Squad'}
            </button>

            {error && <p className={styles.error}>{error}</p>}

            {result && (
              <div className={styles.summary}>
                <div className={styles.summaryRow}>
                  <span>Status</span>
                  <span className={result.status === 'Optimal' ? styles.optimal : styles.infeasible}>{result.status}</span>
                </div>
                <div className={styles.summaryRow}>
                  <span>Total Cost</span>
                  <span>£{result.total_salary.toFixed(1)}m</span>
                </div>
                <div className={styles.summaryRow}>
                  <span>Expected Points</span>
                  <span className={styles.pts}>{result.total_expected_points.toFixed(1)}</span>
                </div>
                <div className={styles.summaryRow}>
                  <span>Formation</span>
                  <span>{result.formation}</span>
                </div>
              </div>
            )}
          </div>

          {/* Pitch + player table */}
          <div className={styles.right}>
            {result?.selected_players?.length ? (
              <>
                <div className={`card ${styles.pitchCard}`}>
                  <PitchLayout players={result.selected_players} />
                </div>
                <div className={`card ${styles.tableCard}`}>
                  <h3 className={styles.tableTitle}>Selected Squad</h3>
                  <table className={styles.table}>
                    <thead>
                      <tr><th>Player</th><th>Team</th><th>Pos</th><th>£m</th><th>xPts</th></tr>
                    </thead>
                    <tbody>
                      {result.selected_players.map(p => (
                        <tr key={p.id}>
                          <td>{p.name}</td>
                          <td className={styles.dim}>{p.team}</td>
                          <td><span className={`${styles.pos} ${styles[`pos${p.position}`]}`}>{p.position}</span></td>
                          <td>{p.salary.toFixed(1)}</td>
                          <td className={styles.pts}>{p.expected_points.toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div className={`card ${styles.empty}`}>
                <div className={styles.emptyIcon}>🏟️</div>
                <p>Click <strong>Optimise Squad</strong> to build your lineup</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
