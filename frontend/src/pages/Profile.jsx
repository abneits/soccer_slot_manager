import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { statsAPI, usersAPI } from '../services/api';

function Profile() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) {
      loadUserStats();
    }
  }, [user]);

  const loadUserStats = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await statsAPI.getByUser(user._id);
      setStats(response.data);
    } catch (err) {
      setError('Failed to load profile statistics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading profile...</div>;
  }

  return (
    <div className="container">
      <div className="card">
        <h2>👤 My Profile</h2>
        {error && <div className="error">{error}</div>}
        
        {user && (
          <div>
            <div style={{ marginBottom: '1.5rem' }}>
              <p><strong>Display Name:</strong> {user.displayName}</p>
              <p><strong>Name:</strong> {user.firstName} {user.lastName}</p>
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>Member Since:</strong> {new Date(user.registrationDate).toLocaleDateString()}</p>
            </div>

            {stats && (
              <>
                <h3>My Statistics</h3>
                <div className="stats-grid">
                  <div className="stat-card" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                    <h3>Sessions Attended</h3>
                    <div className="stat-value">{stats.statistics.attendance}</div>
                    <div className="stat-label">Total matches</div>
                  </div>

                  <div className="stat-card" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                    <h3>Wins</h3>
                    <div className="stat-value">{stats.statistics.wins}</div>
                    <div className="stat-label">Victories</div>
                  </div>

                  <div className="stat-card" style={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }}>
                    <h3>Guests Invited</h3>
                    <div className="stat-value">{stats.statistics.guestsInvited}</div>
                    <div className="stat-label">Total guests</div>
                  </div>

                  <div className="stat-card" style={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }}>
                    <h3>Users Sponsored</h3>
                    <div className="stat-value">{stats.statistics.sponsoredUsers}</div>
                    <div className="stat-label">New members</div>
                  </div>
                </div>

                <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#ecf0f1', borderRadius: '4px' }}>
                  <p style={{ margin: 0 }}>
                    <strong>Total Contributions:</strong> {stats.statistics.totalContributions}
                    <span style={{ marginLeft: '0.5rem', color: '#7f8c8d', fontSize: '0.875rem' }}>
                      (Guests + Sponsored Users)
                    </span>
                  </p>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Profile;
