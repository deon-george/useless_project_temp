import React, { useState, useRef, useEffect, useCallback } from 'react';
import { identifyFace } from '../api';

export default function FaceScan({ onIdentified, onError }) {
  const videoRef = useRef(null);
  const [streaming, setStreaming] = useState(false);
  const [capturedFile, setCapturedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const canvasRef = useRef(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setStreaming(true);
      }
    } catch (error) {
      onError?.(error.message || 'Camera permission was denied.');
    }
  }, [onError]);

  useEffect(() => {
    startCamera();

    return () => {
      const stream = videoRef.current?.srcObject;
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [startCamera]);

  const capture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) {
      return;
    }

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      const file = new File([blob], 'capture.png', { type: 'image/png' });
      setCapturedFile(file);
    }, 'image/png');
  };

  const submit = async () => {
    if (!capturedFile) {
      onError?.('Capture a photo first.');
      return;
    }

    try {
      setLoading(true);
      const data = await identifyFace(capturedFile);
      onIdentified?.(data);
    } catch (error) {
      onError?.(error.message || 'Face identification failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Face scan</h2>
      <video ref={videoRef} autoPlay playsInline muted />
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      <div className="row">
        <button type="button" className="secondary" onClick={startCamera} disabled={streaming}>
          Start camera
        </button>
        <button type="button" className="secondary" onClick={capture} disabled={!streaming}>
          Capture
        </button>
        <button type="button" className="primary" onClick={submit} disabled={!capturedFile || loading}>
          {loading ? 'Identifying...' : 'Identify'}
        </button>
      </div>

      {capturedFile && (
        <div className="capture">
          <h3>Captured preview</h3>
          <img
            className="preview"
            src={URL.createObjectURL(capturedFile)}
            alt="Captured face"
          />
        </div>
      )}
    </div>
  );
}
