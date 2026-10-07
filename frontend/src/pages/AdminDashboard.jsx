import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import ReviewRow from '../components/ReviewRow';

const TABS = ['Review queue', 'Accounts', 'Transactions'];

export default function AdminDashboard({ me, onLogout }) {
  const [tab, setTab] = useState(TABS[0]);
  const [reviews, setReviews] = useState([]);
  const [reviewStatusFilter, setReviewStatusFilter] = useState('PENDING');
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState('');

  const refreshReviews = useCallback(async () => {
    try {
      const data = await api.listReviews(reviewStatusFilter);
      setReviews(data.results ?? data);
    } catch (err) {
      setError(err.message);
    }
  }, [reviewStatusFilter]);

  useEffect(() => {
    if (tab === 'Review queue') refreshReviews();
  }, [tab, refreshReviews]);

  useEffect(() => {
    if (tab === 'Accounts') {
      api.listAccounts().then(setAccounts).catch((err) => setError(err.message));
    }
    if (tab === 'Transactions') {
      api.listTransactions().then(setTransactions).catch((err) => setError(err.message));
    }
  }, [tab]);

  return (
    <div className="page">
      <header className="topbar">
        <h2>Admin console</h2>
        <button className="link-button" onClick={onLogout}>Log out</button>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button key={t} className={t === tab ? 'tab active' : 'tab'} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </nav>

      {error && <div className="error-banner">{error}</div>}

      {tab === 'Review queue' && (
        <section className="card">
          <div className="row-between">
            <h3>Human review queue</h3>
            <select value={reviewStatusFilter} onChange={(e) => setReviewStatusFilter(e.target.value)}>
              <option value="PENDING">PENDING</option>
              <option value="APPROVED">APPROVED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="">ALL</option>
            </select>
          </div>
          {reviews.length === 0 ? (
            <p className="muted">Nothing here.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Entity</th><th>Reasons</th><th>Fields (editable)</th><th>Resolve</th>
                </tr>
              </thead>
              <tbody>
                {reviews.map((r) => (
                  <ReviewRow key={r.id} review={r} adminUsername={me.username} onResolved={refreshReviews} />
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === 'Accounts' && (
        <section className="card">
          <h3>All accounts ({accounts.length})</h3>
          <table>
            <thead>
              <tr>
                <th>Account</th><th>Customer</th><th>Type</th><th>Status</th><th>Balance</th><th>Daily limit</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((a) => (
                <tr key={a.account_id}>
                  <td>{a.account_id}</td>
                  <td>{a.customer_name}</td>
                  <td>{a.account_type}</td>
                  <td>{a.status}</td>
                  <td>{a.currency} {a.balance}</td>
                  <td>{a.currency} {a.daily_limit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'Transactions' && (
        <section className="card">
          <h3>All transactions ({transactions.length})</h3>
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Time</th><th>Type</th><th>From</th><th>To</th><th>Amount</th><th>Channel</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((t) => (
                <tr key={t.transaction_id}>
                  <td>{t.transaction_id}</td>
                  <td>{t.timestamp}</td>
                  <td>{t.type}</td>
                  <td>{t.from_account ?? '—'}</td>
                  <td>{t.to_account ?? '—'}</td>
                  <td>{t.amount}</td>
                  <td>{t.channel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
