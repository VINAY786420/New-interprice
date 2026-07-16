import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const API = process.env.REACT_APP_API_URL || '';

  useEffect(() => {
    // fetch backend root or health endpoint
    const url = API ? `${API}/` : '/';
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json().catch(() => null);
      })
      .then((data) => setInfo(data))
      .catch((err) => setInfo({ error: err.message }))
      .finally(() => setLoading(false));
  }, [API]);

  return (
    <div className="App" style={{ padding: 20, fontFamily: 'Arial, sans-serif' }}>
      <header style={{ marginBottom: 20 }}>
        <h1>Interprice</h1>
        <p>Social Media Data Collection Centre</p>
      </header>

      <section>
        <h2>Dashboard</h2>
        {loading && <p>Loading data from backend…</p>}
        {!loading && !info && <p>No data returned from backend.</p>}
        {!loading && info && info.error && (
          <div style={{ color: 'crimson' }}>
            <strong>API error:</strong> {info.error}
          </div>
        )}
        {!loading && info && !info.error && (
          <pre style={{
            background: '#f6f8fa',
            padding: 12,
            borderRadius: 6,
            overflowX: 'auto',
            maxWidth: '100%',
          }}>
            {JSON.stringify(info, null, 2)}
          </pre>
        )}
      </section>
    </div>
  );
}

export default App;
