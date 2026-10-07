import { useState } from 'react';
import { api } from '../api';

export default function ReviewRow({ review, adminUsername, onResolved }) {
  const [fields, setFields] = useState({ ...review.payload });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  function updateField(key, value) {
    setFields((f) => ({ ...f, [key]: value }));
  }

  function changedOverrides() {
    const overrides = {};
    for (const [key, value] of Object.entries(fields)) {
      if (review.payload[key] !== value) overrides[key] = value;
    }
    return overrides;
  }

  async function handleAdd() {
    setBusy(true);
    setMessage('');
    try {
      const data = await api.addReview(review.id, changedOverrides(), adminUsername);
      if (data.status === 'MIGRATED') {
        setMessage('Migrated.');
      } else {
        setMessage(`Still pending: ${data.reasons?.join('; ')}`);
      }
      onResolved?.();
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleRemove() {
    setBusy(true);
    setMessage('');
    try {
      await api.removeReview(review.id, adminUsername);
      onResolved?.();
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <tr>
      <td>{review.id}</td>
      <td>{review.entity_type}</td>
      <td>
        <ul className="reasons">
          {review.reasons.map((r, i) => <li key={i}>{r}</li>)}
        </ul>
      </td>
      <td>
        <div className="field-grid">
          {Object.entries(fields).map(([key, value]) => (
            <label key={key} className="mini-field">
              {key}
              <input value={value ?? ''} onChange={(e) => updateField(key, e.target.value)} />
            </label>
          ))}
        </div>
      </td>
      <td className="actions">
        <button type="button" disabled={busy} onClick={handleAdd}>Add</button>
        <button type="button" disabled={busy} className="danger" onClick={handleRemove}>Remove</button>
        {message && <div className="muted small">{message}</div>}
      </td>
    </tr>
  );
}
