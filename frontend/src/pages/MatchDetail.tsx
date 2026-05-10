import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { useMatchWebSocket } from '../hooks/useMatchWebSocket'
import ProbabilityChart from '../components/ProbabilityChart'
import ShapWaterfallChart from '../components/ShapWaterfallChart'
import { ArrowLeft, Wifi, WifiOff, Zap, Clock } from 'lucide-react'
import { useRef, useEffect, useState } from 'react'
import type { Prediction } from '../api/client'
import styles from './MatchDetail.module.css'

function ConnectionStatus({ connected, reconnectCount }: { connected: boolean; reconnectCount: number }) {
  return (
    <div className={`${styles.connStatus} ${connected ? styles.connected : styles.disconnected}`}>
      {connected ? <Wifi size={13} /> : <WifiOff size={13} />}
      {connected ? 'Live' : reconnectCount > 0 ? `Reconnecting…` : 'Connecting…'}
    </div>
  )
}

function ProbabilityBar({ home, draw, away, homeTeam, awayTeam }: {
  home: number; draw: number; away: number; homeTeam: string; awayTeam: string
}) {
  return (
    <div className={styles.probSection}>
      <div className={styles.probLabels}>
        <div className={styles.probLabel}>
          <span className={styles.probTeam}>{homeTeam}</span>
          <span className={styles.probValue} style={{ color: 'var(--color-green)' }}>
            {(home * 100).toFixed(1)}%
          </span>
        </div>
        <div className={`${styles.probLabel} ${styles.probCenter}`}>
          <span className={styles.probTeam}>Draw</span>
          <span className={styles.probValue} style={{ color: 'var(--color-amber)' }}>
            {(draw * 100).toFixed(1)}%
          </span>
        </div>
        <div className={`${styles.probLabel} ${styles.probRight}`}>
          <span className={styles.probTeam}>{awayTeam}</span>
          <span className={styles.probValue} style={{ color: 'var(--color-red)' }}>
            {(away * 100).toFixed(1)}%
          </span>
        </div>
      </div>
      <div className="prob-bar-wrap">
        <div className="prob-bar-home" style={{ width: `${home * 100}%` }} />
        <div className="prob-bar-draw" style={{ width: `${draw * 100}%` }} />
        <div className="prob-bar-away" style={{ flex: 1 }} />
      </div>
    </div>
  )
}

export default function MatchDetail() {
  const { id } = useParams<{ id: string }>()
  const matchId = parseInt(id ?? '0')

  const { data: match } = useQuery({
    queryKey: ['match', matchId],
    queryFn: () => api.getMatch(matchId),
    enabled: !!matchId,
  })

  const { prediction: wsPrediction, isConnected, reconnectCount } = useMatchWebSocket(
    match?.status === 'live' ? matchId : null
  )

  // For non-live matches, load prediction via REST
  const { data: restPrediction } = useQuery({
    queryKey: ['prediction', matchId],
    queryFn: () => api.getPrediction(matchId),
    enabled: !!matchId && match?.status !== 'live',
  })

  const prediction = wsPrediction ?? restPrediction ?? null

  // Track prediction history for the line chart
  const [history, setHistory] = useState<Array<{ minute: number; home: number; draw: number; away: number }>>([])
  const historyRef = useRef(history)
  historyRef.current = history

  useEffect(() => {
    if (!prediction) return
    const last = historyRef.current[historyRef.current.length - 1]
    if (last?.minute === prediction.minute) return
    setHistory(prev => [
      ...prev.slice(-60),   // keep last 60 data points
      {
        minute: prediction.minute,
        home: prediction.prob_home_win,
        draw: prediction.prob_draw,
        away: prediction.prob_away_win,
      }
    ])
  }, [prediction])

  const home = match?.home_team ?? '—'
  const away = match?.away_team ?? '—'

  return (
    <div className="page">
      <div className="container">
        {/* Back */}
        <Link to="/" className={styles.back}>
          <ArrowLeft size={16} /> All Matches
        </Link>

        {/* Match header */}
        <div className={`card ${styles.header} animate-fade-in`}>
          <div className={styles.headerTop}>
            <span className={styles.league}>{match?.league ?? '—'}</span>
            {match?.status === 'live' && <ConnectionStatus connected={isConnected} reconnectCount={reconnectCount} />}
            {match?.status && match.status !== 'live' && (
              <span className={`badge badge-${match.status}`}>{match.status}</span>
            )}
          </div>

          <div className={styles.matchRow}>
            <div className={styles.teamBlock}>
              <div className={styles.avatar}>{home[0]}{home.split(' ').slice(-1)[0][0]}</div>
              <span className={styles.teamName}>{home}</span>
            </div>

            <div className={styles.scoreBlock}>
              <div className={styles.scoreMain}>
                <span>{prediction?.home_goals ?? match?.home_goals ?? 0}</span>
                <span className={styles.scoreSep}>–</span>
                <span>{prediction?.away_goals ?? match?.away_goals ?? 0}</span>
              </div>
              {prediction && (
                <div className={styles.minute}>
                  <Clock size={12} />
                  {prediction.minute}'
                </div>
              )}
            </div>

            <div className={`${styles.teamBlock} ${styles.teamRight}`}>
              <div className={styles.avatar}>{away[0]}{away.split(' ').slice(-1)[0][0]}</div>
              <span className={styles.teamName}>{away}</span>
            </div>
          </div>

          {prediction && (
            <ProbabilityBar
              home={prediction.prob_home_win}
              draw={prediction.prob_draw}
              away={prediction.prob_away_win}
              homeTeam={home}
              awayTeam={away}
            />
          )}
        </div>

        {/* Inference badge */}
        {prediction?.inference_ms !== undefined && (
          <div className={styles.inferenceBadge}>
            <Zap size={12} />
            Model inference: {prediction.inference_ms}ms
          </div>
        )}

        {/* Charts */}
        <div className={`grid-2 ${styles.charts}`}>
          {/* Probability timeline */}
          <div className={`card ${styles.chartCard}`}>
            <h2 className={styles.chartTitle}>Win Probability Over Time</h2>
            {history.length === 0 ? (
              <div className={styles.chartEmpty}>
                Waiting for match data…
              </div>
            ) : (
              <ProbabilityChart data={history} homeTeam={home} awayTeam={away} />
            )}
          </div>

          {/* SHAP waterfall */}
          <div className={`card ${styles.chartCard}`}>
            <h2 className={styles.chartTitle}>
              What Drives This Prediction?
              <span className={styles.shapLabel}>SHAP Feature Impact</span>
            </h2>
            {prediction?.shap_features?.length ? (
              <ShapWaterfallChart features={prediction.shap_features} homeTeam={home} />
            ) : (
              <div className={styles.chartEmpty}>Waiting for SHAP values…</div>
            )}
          </div>
        </div>

        {/* Stats row */}
        {prediction && (
          <div className={`card ${styles.statsCard} animate-fade-in`}>
            <h3 className={styles.statsTitle}>Match Stats</h3>
            <div className={styles.statsGrid}>
              {prediction.shap_features.slice(0, 6).map(f => (
                <div className="stat-pill" key={f.feature}>
                  <span className="value">{f.raw_value}</span>
                  <span className="label">{f.feature.replace(/_/g, ' ')}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
