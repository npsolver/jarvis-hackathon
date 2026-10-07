import { useEffect, useState } from 'react';
import { api } from './api';
import Login from './pages/Login';
import UserDashboard from './pages/UserDashboard';
import AdminDashboard from './pages/AdminDashboard';

function loadStoredMe() {
  const raw = localStorage.getItem('me');
  return raw ? JSON.parse(raw) : null;
}

export default function App() {
  const [me, setMe] = useState(loadStoredMe);
  const [checking, setChecking] = useState(!!localStorage.getItem('token'));

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      setChecking(false);
      return;
    }
    api.me()
      .then((data) => {
        setMe(data);
        localStorage.setItem('me', JSON.stringify(data));
      })
      .catch(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('me');
        setMe(null);
      })
      .finally(() => setChecking(false));
  }, []);

  function handleLogin(data) {
    localStorage.setItem('token', data.token);
    const meData = { username: data.username, role: data.role, account_id: data.account_id };
    localStorage.setItem('me', JSON.stringify(meData));
    setMe(meData);
  }

  async function handleLogout() {
    try {
      await api.logout();
    } catch {
      // token may already be invalid; clear local state regardless
    }
    localStorage.removeItem('token');
    localStorage.removeItem('me');
    setMe(null);
  }

  if (checking) return <div className="centered-page">Loading…</div>;
  if (!me) return <Login onLogin={handleLogin} />;
  if (me.role === 'ADMIN') return <AdminDashboard me={me} onLogout={handleLogout} />;
  return <UserDashboard me={me} onLogout={handleLogout} />;
}
