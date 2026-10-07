import { useState } from 'react';
import { api, ApiError } from '../api';

function generateTransactionId() {
  return `TX-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`.toUpperCase();
}

function nowAsCsvTimestamp() {
  return new Date().toISOString().slice(0, 19);
}

const TYPES = ['DEPOSIT', 'WITHDRAWAL', 'PURCHASE', 'TRANSFER', 'REVERSAL'];
const CHANNELS = ['ONLINE', 'POS', 'ATM', 'PARTNER_FI'];

export default function TransactionForm({ ownAccountId, onSubmitted }) {
  const [type, setType] = useState('TRANSFER');
  const [counterparty, setCounterparty] = useState('');
  const [amount, setAmount] = useState('');
  const [channel, setChannel] = useState('ONLINE');
  const [description, setDescription] = useState('');
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const needsFrom = ['WITHDRAWAL', 'PURCHASE', 'TRANSFER'].includes(type);
  const needsCounterpartyTo = ['TRANSFER', 'DEPOSIT'].includes(type);

  async function handleSubmit(e) {
    e.preventDefault();
    setResult(null);
    setSubmitting(true);

    const payload = {
      transactionId: generateTransactionId(),
      timestamp: nowAsCsvTimestamp(),
      type,
      fromAccount: needsFrom ? ownAccountId : '',
      toAccount: needsCounterpartyTo ? counterparty.trim() : (type === 'WITHDRAWAL' || type === 'PURCHASE' ? '' : counterparty.trim()),
      amount,
      channel,
      description,
    };
    // DEPOSIT with no explicit counterparty deposits into the user's own account.
    if (type === 'DEPOSIT' && !payload.toAccount) payload.toAccount = ownAccountId;

    try {
      const data = await api.createTransaction(payload);
      setResult({ ok: true, data });
      setAmount('');
      setDescription('');
      onSubmitted?.();
    } catch (err) {
      const reasons = err instanceof ApiError ? err.body?.reasons : null;
      setResult({ ok: false, message: err.message, reasons });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h3>New transaction</h3>

      <label>
        Type
        <select value={type} onChange={(e) => setType(e.target.value)}>
          {TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </label>

      {needsFrom && (
        <label>
          From account
          <input value={ownAccountId} disabled />
        </label>
      )}

      {(type === 'TRANSFER' || type === 'REVERSAL' || type === 'DEPOSIT') && (
        <label>
          {type === 'DEPOSIT' ? 'To account (default: your own)' : 'To account'}
          <input
            value={counterparty}
            onChange={(e) => setCounterparty(e.target.value)}
            placeholder={type === 'DEPOSIT' ? ownAccountId : 'ACC1002'}
          />
        </label>
      )}

      <label>
        Amount
        <input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="50.00" required />
      </label>

      <label>
        Channel
        <select value={channel} onChange={(e) => setChannel(e.target.value)}>
          {CHANNELS.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </label>

      <label>
        Description
        <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional" />
      </label>

      <button type="submit" disabled={submitting}>
        {submitting ? 'Submitting…' : 'Submit transaction'}
      </button>

      {result && result.ok && result.data.status === 'PENDING_REVIEW' && (
        <div className="warn-banner">
          Sent for human review: {result.data.reasons?.join('; ')}
        </div>
      )}
      {result && result.ok && !result.data.status && (
        <div className="success-banner">Transaction completed.</div>
      )}
      {result && !result.ok && (
        <div className="error-banner">
          {result.message}
          {result.reasons?.length ? ` (${result.reasons.join('; ')})` : ''}
        </div>
      )}
    </form>
  );
}
