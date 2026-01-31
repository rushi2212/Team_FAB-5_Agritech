import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getMe } from '../api';

export default function Navbar() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    getMe()
      .then((d) => setUser(d.user))
      .catch(() => setUser(null));
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    navigate('/');
  };

  return (
    <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-earth-200/80 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl font-display font-bold text-farm-700">Crop Calendar</span>
            <span className="text-earth-500 text-sm hidden sm:inline">Smart Farming</span>
          </Link>
          <div className="flex items-center gap-3">
            {user ? (
              <>
                <Link
                  to="/dashboard"
                  className="text-earth-600 hover:text-farm-600 font-medium transition"
                >
                  Dashboard
                </Link>
                <span className="text-earth-500 text-sm hidden sm:inline">{user.name}</span>
                <button
                  onClick={logout}
                  className="rounded-xl px-4 py-2 text-earth-600 hover:bg-earth-100 font-medium transition"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="rounded-xl px-4 py-2 text-earth-600 hover:bg-earth-100 font-medium transition"
                >
                  Login
                </Link>
                <Link to="/register" className="btn-primary">
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
