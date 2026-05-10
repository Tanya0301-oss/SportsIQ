import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Activity, Users, Trophy } from 'lucide-react'
import MatchList from './pages/MatchList'
import MatchDetail from './pages/MatchDetail'
import LineupOptimizer from './pages/LineupOptimizer'
import styles from './App.module.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className={styles.app}>
        <nav className={styles.nav}>
          <div className={`container ${styles.navInner}`}>
            <NavLink to="/" className={styles.logo}>
              <span className={styles.logoIcon}>⚽</span>
              <span>SportIQ</span>
            </NavLink>
            <div className={styles.navLinks}>
              <NavLink to="/" end className={({ isActive }) => `${styles.navLink} ${isActive ? styles.active : ''}`}>
                <Activity size={16} />
                Matches
              </NavLink>
              <NavLink to="/lineup" className={({ isActive }) => `${styles.navLink} ${isActive ? styles.active : ''}`}>
                <Users size={16} />
                Lineup
              </NavLink>
            </div>
          </div>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<MatchList />} />
            <Route path="/match/:id" element={<MatchDetail />} />
            <Route path="/lineup" element={<LineupOptimizer />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
