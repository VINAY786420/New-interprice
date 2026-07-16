import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reqUrl, setReqUrl] = useState('');
  const [status, setStatus] = useState(null);
  const [raw, setRaw] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const API = process.env.REACT_APP_API_URL || '';

  useEffect(() => {
    const url = API ? `${API}/` : '/';
    setReqUrl(url);
    setLoading(true);
    setStatus(null);
    setRaw('');
    setErrorMsg('');

    fetch(url)
      .then(async (r) => {
        setStatus(r.status);
        const text = await r.text().catch(() => '');
        setRaw(text);
        // try parse JSON
        try {
          const json = JSON.parse(text);
          setInfo(json);
        } catch (e) {
          setInfo(null);
        }
      })
      .catch((err) => {
        setErrorMsg(err.message || String(err));
      })
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

        <div style={{ marginBottom: 12 }}>
          <strong>Build-time API variable (REACT_APP_API_URL):</strong>
          <div style={{ background: '#f6f8fa', padding: 8, borderRadius: 6, marginTop: 6 }}>{API || '(empty)'}</div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <strong>Request URL:</strong>
          <div style={{ background: '#f6f8fa', padding: 8, borderRadius: 6, marginTop: 6 }}>{reqUrl}</div>
        </div>

        {loading && <p>Loading data from backend…</p>}

        {!loading && errorMsg && (
          <div style={{ color: 'crimson' }}>
            <strong>Fetch error:</strong> {errorMsg}
          </div>
        )}

        {!loading && status !== null && (
          <div style={{ marginTop: 12 }}>
            <strong>HTTP status:</strong> {status}
          </div>
        )}

        {!loading && raw && (
          <div style={{ marginTop: 12 }}>
            <strong>Raw response (first 10k chars):</strong>
            <pre style={{ background: '#f6f8fa', padding: 12, borderRadius: 6, overflowX: 'auto', maxWidth: '100%' }}>
              {raw.slice(0, 10000)}
            </pre>
          </div>
        )}

        {!loading && info && (
          <div style={{ marginTop: 12 }}>
            <strong>Parsed JSON:</strong>
            <pre style={{ background: '#f6f8fa', padding: 12, borderRadius: 6, overflowX: 'auto' }}>
              {JSON.stringify(info, null, 2)}
            </pre>
          </div>
        )}

        {!loading && !info && !raw && !errorMsg && (
          <div style={{ color: '#666' }}>No data returned from backend.</div>
        )}
      </section>
    </div>
  );
}

export default App;
