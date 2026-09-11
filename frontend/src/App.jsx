import React, { useState, useRef, useEffect } from 'react';
import FaceScan from './components/FaceScan';
import PaymentForm from './components/PaymentForm';
import Receipt from './components/Receipt';
import './App.css';

const STEPS = {
  FACE_SCAN: 'FACE_SCAN',
  PAYMENT: 'PAYMENT',
  RECEIPT: 'RECEIPT',
};

export default function App() {
  const [step, setStep] = useState(STEPS.FACE_SCAN);
  const [identity, setIdentity] = useState(null);
  const [receipt, setReceipt] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null);
  }, [step]);

  const handleIdentified = (data) => {
    setIdentity(data);
    setStep(STEPS.PAYMENT);
  };

  const handlePaid = (data) => {
    setReceipt(data);
    setStep(STEPS.RECEIPT);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>FacePay</h1>
        <nav className="app-nav">
          <button
            type="button"
            className={step === STEPS.FACE_SCAN ? 'active' : ''}
            onClick={() => setStep(STEPS.FACE_SCAN)}
          >
            Scan
          </button>
          <button
            type="button"
            className={step === STEPS.PAYMENT ? 'active' : ''}
            disabled={!identity}
            onClick={() => identity && setStep(STEPS.PAYMENT)}
          >
            Pay
          </button>
          <button
            type="button"
            className={step === STEPS.RECEIPT ? 'active' : ''}
            disabled={!receipt}
            onClick={() => receipt && setStep(STEPS.RECEIPT)}
          >
            Receipt
          </button>
        </nav>
      </header>

      {error && <div className="app-error" role="alert">{error}</div>}

      <main>
        {step === STEPS.FACE_SCAN && (
          <FaceScan onIdentified={handleIdentified} onError={setError} />
        )}
        {step === STEPS.PAYMENT && (
          <PaymentForm identity={identity} onPaid={handlePaid} onError={setError} />
        )}
        {step === STEPS.RECEIPT && (
          <Receipt receipt={receipt} onReset={() => { setStep(STEPS.FACE_SCAN); setIdentity(null); setReceipt(null); }} />
        )}
      </main>
    </div>
  );
}
