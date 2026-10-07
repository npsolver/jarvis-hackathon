import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import TransactionForm from '../components/TransactionForm';

export default function UserDashboard({ me, onLogout }) {
  const [account, setAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    try {
      const [acc, txs] = await Promise.all([
        api.getAccount(me.account_id),
        api.listTransactions(),
      ]);
      setAccount(acc);
      setTransactions(txs);
    } catch (err) {
      setError(err.message);
    }
  }, [me.account_id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="page">
      <header className="topbar">
        <h2>Hi, {account?.customer_name ?? me.username}</h2>
        <button className="link-button" onClick={onLogout}>Log out</button>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid">
        <section className="card">
          <h3>My account</h3>
          {account ? (
            <dl className="kv">
              <dt>Account</dt><dd>{account.account_id}</dd>
              <dt>Type</dt><dd>{account.account_type}</dd>
              <dt>Status</dt><dd>{account.status}</dd>
              <dt>Balance</dt><dd>{account.currency} {account.balance}</dd>
              <dt>Daily limit</dt><dd>{account.currency} {account.daily_limit}</dd>
            </dl>
          ) : (
            <p className="muted">Loading…</p>
          )}
        </section>

        <TransactionForm ownAccountId={me.account_id} onSubmitted={refresh} />
      </div>

      <section className="card">
        <h3>My transactions</h3>
        {transactions.length === 0 ? (
          <p className="muted">No transactions yet.</p>
        ) : (
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
        )}
      </section>
    </div>
  );
}
