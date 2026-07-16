import React, { useState, useEffect } from 'react';
import './Admin.css';

function Admin() {
  const [stats, setStats] = useState({
    totalData: 0,
    scrapers: 0,
    lastUpdate: new Date()
  });

  useEffect(() => {
    // Fetch stats from backend
    fetch('/api/v1/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Error fetching stats:', err));
  }, []);

  return (
    <div className="Admin">
      <header className="Admin-header">
        <h1>Interprice Admin Panel</h1>
      </header>
      <main className="Admin-main">
        <section className="Stats">
          <div className="Stat-card">
            <h3>Total Data Points</h3>
            <p className="Stat-value">{stats.totalData}</p>
          </div>
          <div className="Stat-card">
            <h3>Active Scrapers</h3>
            <p className="Stat-value">{stats.scrapers}</p>
          </div>
          <div className="Stat-card">
            <h3>Last Update</h3>
            <p className="Stat-value">{stats.lastUpdate?.toString().split('T')[0]}</p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default Admin;