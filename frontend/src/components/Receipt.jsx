import React from 'react';

export default function Receipt({ receipt, onReset }) {
  if (!receipt) {
    return null;
  }

  return (
    <div className="card">
      <h2>Receipt</h2>
      <pre>{JSON.stringify(receipt, null, 2)}</pre>
      <div className="row">
        <button type="button" className="secondary" onClick={onReset}>
          New payment
        </button>
      </div>
    </div>
  );
}
