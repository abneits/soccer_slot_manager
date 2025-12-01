import { useState, useEffect } from 'react';
import { statsAPI } from '../services/api';

function Statistics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await statsAPI.getAll();
      setStats(response.data);
    } catch (err) {
      setError('Failed to load statistics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading statistics...</div>;
  }

  if (error) {
    return <div className="container"><div className="error">{error}</div></div>;
  }

  return (
    <div className="container">
      <div className="card">
        <h2>🏆 Player Statistics</h2>
        
        <div className="stats-grid">
          {stats?.statistics?.mostWins && (
            <div className="stat-card" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
              <h3>Most Wins</h3>
              <div className="stat-value">{stats.statistics.mostWins.wins}</div>
              <div className="stat-label">{stats.statistics.mostWins.displayName}</div>
            </div>
          )}

          {stats?.statistics?.bestAttendance && (
            <div className="stat-card" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
              <h3>Best Attendance</h3>
              <div className="stat-value">{stats.statistics.bestAttendance.attendance}</div>
              <div className="stat-label">{stats.statistics.bestAttendance.displayName}</div>
            </div>
          )}

          {stats?.statistics?.topContributor && (
            <div className="stat-card" style={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }}>
              <h3>Top Contributor</h3>
              <div className="stat-value">{stats.statistics.topContributor.guestsInvited}</div>
              <div className="stat-label">{stats.statistics.topContributor.displayName}</div>
            </div>
          )}
        </div>

        <h3 style={{ marginTop: '2rem' }}>All Player Stats</h3>
        {stats?.allStats && stats.allStats.length > 0 ? (
          <table style={{ width: '100%', marginTop: '1rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                <th style={{ padding: '0.75rem' }}>Player</th>
                <th style={{ padding: '0.75rem' }}>Attendance</th>
                <th style={{ padding: '0.75rem' }}>Wins</th>
                <th style={{ padding: '0.75rem' }}>Contributions</th>
              </tr>
            </thead>
            <tbody>
              {stats.allStats.map((player) => (
                <tr key={player.userId} style={{ borderBottom: '1px solid #ecf0f1' }}>
                  <td style={{ padding: '0.75rem' }}>
                    <strong>{player.displayName}</strong>
                    <div style={{ fontSize: '0.875rem', color: '#7f8c8d' }}>
                      {player.firstName} {player.lastName}
                    </div>
                  </td>
                  <td style={{ padding: '0.75rem' }}>{player.attendance}</td>
                  <td style={{ padding: '0.75rem' }}>{player.wins}</td>
                  <td style={{ padding: '0.75rem' }}>{player.guestsInvited}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No statistics available yet.</p>
        )}
      </div>
    </div>
  );
}

export default Statistics;
