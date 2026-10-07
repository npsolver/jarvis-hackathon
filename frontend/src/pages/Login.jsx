import { useState } from 'react';
import { api } from '../api';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await api.login(username.trim(), password);
      onLogin(data);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  function fillDemo(user, pass) {
    setUsername(user);
    setPassword(pass);
  }

  return (
    <div className="centered-page">
      <form className="card login-card" onSubmit={handleSubmit}>
        <h1>Jarvis Banking</h1>
        <p className="muted">Sign in as a customer or an admin.</p>

        <label>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="e.g. ACC1001 or admin"
            autoFocus
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && <div className="error-banner">{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign in'}
        </button>

        <div className="demo-hints">
          <button type="button" className="link-button" onClick={() => fillDemo('admin', 'admin123')}>
            Use admin demo login
          </button>
          <button type="button" className="link-button" onClick={() => fillDemo('ACC1001', 'password123')}>
            Use customer demo login (ACC1001)
          </button>
        </div>
      </form>
    </div>
  );
}
