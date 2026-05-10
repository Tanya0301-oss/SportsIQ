import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api, type Match } from '../api/client'
import { Calendar, MapPin, TrendingUp, ChevronRight } from 'lucide-react'
import styles from './MatchList.module.css'

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{status}</span>
}

function FormDot({ win }: { win: boolean }) {
  return (
    <span
      style={{
        width: 8, height: 8, borderRadius: '50%', display: 'inline-block',
        background: win ? 'var(--color-green)' : 'var(--color-red)',
        boxShadow: win ? '0 0 4px var(--color-green)' : '0 0 4px var(--color-red)',
      }}
    />
  )
}

function MatchCard({ match }: { match: Match }) {
  const homeForm = Math.round(match.home_form * 5)
  const awayForm = Math.round(match.away_form * 5)

  return (
    <Link to={`/match/${match.id}`} className={`card ${styles.card}`}>
      <div className={styles.cardHeader}>
        <span className={styles.league}>{match.league}</span>
        <StatusBadge status={match.status} />
      </div>

      <div className={styles.teams}>
        <div className={styles.team}>
          <div className={styles.teamAvatar}>{match.home_team[0]}{match.home_team.split(' ').slice(-1)[0][0]}</div>
          <span className={styles.teamName}>{match.home_team}</span>
          <div className={styles.form}>
            {Array.from({ length: 5 }).map((_, i) => (
              <FormDot key={i} win={i < homeForm} />
            ))}
          </div>
        </div>

        <div className={styles.score}>
          {match.status === 'live' || match.status === 'finished' ? (
            <div className={styles.scoreNumbers}>
              <span className={match.home_goals > match.away_goals ? styles.scoreWin : ''}>
                {match.home_goals}
              </span>
              <span className={styles.scoreDash}>–</span>
              <span className={match.away_goals > match.home_goals ? styles.scoreWin : ''}>
                {match.away_goals}
              </span>
            </div>
          ) : (
            <span className={styles.vs}>VS</span>
          )}
        </div>

        <div className={`${styles.team} ${styles.teamRight}`}>
          <div className={styles.teamAvatar}>{match.away_team[0]}{match.away_team.split(' ').slice(-1)[0][0]}</div>
          <span className={styles.teamName}>{match.away_team}</span>
          <div className={styles.form}>
            {Array.from({ length: 5 }).map((_, i) => (
              <FormDot key={i} win={i < awayForm} />
            ))}
          </div>
        </div>
      </div>

      <div className={styles.cardFooter}>
        <span className={styles.meta}>
          <MapPin size={12} />
          {match.venue}
        </span>
        <span className={`${styles.meta} ${styles.metaRight}`}>
          View Analysis <ChevronRight size={14} />
        </span>
      </div>
    </Link>
  )
}

function SkeletonCard() {
  return (
    <div className={`card ${styles.card}`}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <div className="skeleton" style={{ width: 80, height: 18 }} />
        <div className="skeleton" style={{ width: 50, height: 18, marginLeft: 'auto' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <div className="skeleton" style={{ width: 120, height: 40 }} />
        <div className="skeleton" style={{ width: 60, height: 40 }} />
        <div className="skeleton" style={{ width: 120, height: 40 }} />
      </div>
      <div className="skeleton" style={{ width: '100%', height: 14 }} />
    </div>
  )
}

export default function MatchList() {
  const { data: matches, isLoading, error } = useQuery({
    queryKey: ['matches'],
    queryFn: api.getMatches,
    refetchInterval: 15_000,
  })

  const live = matches?.filter(m => m.status === 'live') ?? []
  const scheduled = matches?.filter(m => m.status === 'scheduled') ?? []
  const finished = matches?.filter(m => m.status === 'finished') ?? []

  return (
    <div className="page">
      <div className="container">
        {/* Hero */}
        <div className={`${styles.hero} animate-fade-in`}>
          <h1 className={styles.heroTitle}>
            Live Match<br />
            <span className={styles.heroAccent}>Intelligence</span>
          </h1>
          <p className={styles.heroSub}>
            AI-powered win probabilities updated every few seconds.
            Understand <em>why</em> — not just what.
          </p>
        </div>

        {error && (
          <div className={styles.error}>
            <span>⚠️ Could not connect to backend. Make sure the FastAPI server is running on port 8000.</span>
          </div>
        )}

        {/* Live matches */}
        {(isLoading || live.length > 0) && (
          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>
                <span className={styles.dot} /> Live Now
              </h2>
              <span className={styles.sectionCount}>{live.length}</span>
            </div>
            <div className="grid-auto">
              {isLoading
                ? Array.from({ length: 2 }).map((_, i) => <SkeletonCard key={i} />)
                : live.map(m => <MatchCard key={m.id} match={m} />)
              }
            </div>
          </section>
        )}

        {/* Scheduled */}
        {(isLoading || scheduled.length > 0) && (
          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>
                <Calendar size={18} /> Upcoming
              </h2>
              <span className={styles.sectionCount}>{scheduled.length}</span>
            </div>
            <div className="grid-auto">
              {isLoading
                ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
                : scheduled.map(m => <MatchCard key={m.id} match={m} />)
              }
            </div>
          </section>
        )}

        {/* Finished */}
        {finished.length > 0 && (
          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>
                <TrendingUp size={18} /> Finished
              </h2>
              <span className={styles.sectionCount}>{finished.length}</span>
            </div>
            <div className="grid-auto">
              {finished.map(m => <MatchCard key={m.id} match={m} />)}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
