import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Navbar() {
  const { user, logout } = useAuth();

  return (
    <div className="navbar">
      <h1>⚽ Indoor Football</h1>
      {user && (
        <nav>
          <Link to="/">Home</Link>
          <Link to="/statistics">Statistics</Link>
          <Link to="/profile">Profile</Link>
          <button onClick={logout}>Logout</button>
        </nav>
      )}
    </div>
  );
}

export default Navbar;
