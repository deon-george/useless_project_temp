const BASE_URL = '/api';

async function handleResponse(response) {
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }

  if (!response.ok) {
    const message = data?.detail || data?.message || text || `HTTP ${response.status}`;
    throw new Error(message);
  }

  return data;
}

export async function identifyFace(file) {
  const form = new FormData();
  form.append('file', file);

  const response = await fetch(`${BASE_URL}/identify`, {
    method: 'POST',
    body: form,
  });

  return handleResponse(response);
}

export async function pay({ amount, payee, note = '' }) {
  const response = await fetch(`${BASE_URL}/pay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, payee, note }),
  });

  return handleResponse(response);
}
