import React, { useState } from 'react';
import { pay } from '../api';

export default function PaymentForm({ identity, onPaid, onError }) {
  const [amount, setAmount] = useState('');
  const [payee, setPayee] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();

    if (!amount || !payee) {
      onError?.('Amount and payee UPI are required.');
      return;
    }

    try {
      setLoading(true);
      const data = await pay({ amount, payee, note });
      onPaid?.(data);
    } catch (error) {
      onError?.(error.message || 'Payment failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Payment</h2>
      {identity && (
        <div className="identity">
          <p>
            <strong>Identified:</strong> {identity.name || 'User'} | confidence:{' '}
            {identity.confidence ?? 'n/a'}
          </p>
        </div>
      )}
      <form className="payment-form" onSubmit={submit}>
        <label>
          Amount
          <input
            type="number"
            min="1"
            step="0.01"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </label>
        <label>
          Payee UPI
          <input
            value={payee}
            onChange={(event) => setPayee(event.target.value)}
            placeholder="user@bank"
          />
        </label>
        <label>
          Note
          <input
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Optional"
          />
        </label>
        <div className="row">
          <button type="submit" className="primary" disabled={loading}>
            {loading ? 'Paying...' : 'Confirm'}
          </button>
        </div>
      </form>
    </div>
  );
}
