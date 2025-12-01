import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { slotsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

function Home() {
  const [slot, setSlot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [guests, setGuests] = useState(['']);
  const [isRegistered, setIsRegistered] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    loadNextSlot();
  }, []);

  const loadNextSlot = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await slotsAPI.getNext();
      setSlot(response.data.slot);
      
      // Check if current user is registered
      const userReg = response.data.slot.registrations.find(
        reg => reg.userId._id === user._id
      );
      
      if (userReg) {
        setIsRegistered(true);
        setGuests(userReg.guests.length > 0 ? userReg.guests : ['']);
      }
    } catch (err) {
      setError('Failed to load slot information');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    try {
      const cleanGuests = guests.filter(g => g.trim());
      await slotsAPI.register(slot._id, cleanGuests);
      await loadNextSlot();
      setEditMode(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to register');
    }
  };

  const handleUpdateRegistration = async () => {
    try {
      const cleanGuests = guests.filter(g => g.trim());
      await slotsAPI.updateRegistration(slot._id, cleanGuests);
      await loadNextSlot();
      setEditMode(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update registration');
    }
  };

  const handleCancelRegistration = async () => {
    if (!window.confirm('Are you sure you want to cancel your registration?')) {
      return;
    }

    try {
      await slotsAPI.cancelRegistration(slot._id);
      await loadNextSlot();
      setGuests(['']);
      setEditMode(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to cancel registration');
    }
  };

  const addGuestField = () => {
    setGuests([...guests, '']);
  };

  const removeGuestField = (index) => {
    const newGuests = guests.filter((_, i) => i !== index);
    setGuests(newGuests.length > 0 ? newGuests : ['']);
  };

  const updateGuest = (index, value) => {
    const newGuests = [...guests];
    newGuests[index] = value;
    setGuests(newGuests);
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="container">
      <div className="card">
        <h2>Next Wednesday Session</h2>
        {error && <div className="error">{error}</div>}
        
        {slot && (
          <>
            <p><strong>Date:</strong> {format(new Date(slot.date), 'MMMM dd, yyyy - HH:mm')}</p>
            <p><strong>Total Participants:</strong> {slot.registrations.reduce((acc, reg) => acc + 1 + reg.guests.length, 0)}</p>

            <h3>Registrations</h3>
            {slot.registrations.length === 0 ? (
              <p>No registrations yet. Be the first to register!</p>
            ) : (
              <ul className="player-list">
                {slot.registrations.map((reg) => (
                  <li key={reg._id} className="player-item">
                    <div>
                      <span className="player-name">{reg.userId.displayName}</span>
                      {reg.guests.length > 0 && (
                        <span className="guest-badge">+{reg.guests.length} guest{reg.guests.length > 1 ? 's' : ''}</span>
                      )}
                    </div>
                    {reg.guests.length > 0 && (
                      <div style={{ fontSize: '0.875rem', color: '#7f8c8d', marginTop: '0.25rem' }}>
                        Guests: {reg.guests.join(', ')}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}

            {!isRegistered && !editMode && (
              <div style={{ marginTop: '1.5rem' }}>
                <button className="btn btn-success" onClick={() => setEditMode(true)}>
                  Register for this session
                </button>
              </div>
            )}

            {isRegistered && !editMode && (
              <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                <button className="btn btn-primary" onClick={() => setEditMode(true)}>
                  Edit Registration
                </button>
                <button className="btn btn-danger" onClick={handleCancelRegistration}>
                  Cancel Registration
                </button>
              </div>
            )}

            {editMode && (
              <div style={{ marginTop: '1.5rem' }}>
                <h3>Add Guests (Optional)</h3>
                {guests.map((guest, index) => (
                  <div key={index} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <input
                      type="text"
                      placeholder={`Guest ${index + 1} name`}
                      value={guest}
                      onChange={(e) => updateGuest(index, e.target.value)}
                      style={{ flex: 1, padding: '0.5rem', borderRadius: '4px', border: '1px solid #ddd' }}
                    />
                    {guests.length > 1 && (
                      <button 
                        className="btn btn-danger" 
                        onClick={() => removeGuestField(index)}
                        style={{ padding: '0.5rem 1rem' }}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}
                <button className="btn btn-secondary" onClick={addGuestField} style={{ marginTop: '0.5rem' }}>
                  Add Another Guest
                </button>

                <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
                  {isRegistered ? (
                    <>
                      <button className="btn btn-primary" onClick={handleUpdateRegistration}>
                        Update Registration
                      </button>
                      <button className="btn btn-secondary" onClick={() => setEditMode(false)}>
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button className="btn btn-success" onClick={handleRegister}>
                        Confirm Registration
                      </button>
                      <button className="btn btn-secondary" onClick={() => setEditMode(false)}>
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {slot.details?.finalScore && (
              <>
                <h3 style={{ marginTop: '2rem' }}>Match Results</h3>
                <p><strong>Final Score:</strong> {slot.details.finalScore}</p>
                
                {slot.details.teams && (slot.details.teams.teamA?.length > 0 || slot.details.teams.teamB?.length > 0) && (
                  <div className="teams-container">
                    <div className="team team-a">
                      <h4>Team A</h4>
                      <ul>
                        {slot.details.teams.teamA?.map((player, idx) => (
                          <li key={idx}>{player}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="team team-b">
                      <h4>Team B</h4>
                      <ul>
                        {slot.details.teams.teamB?.map((player, idx) => (
                          <li key={idx}>{player}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Home;
