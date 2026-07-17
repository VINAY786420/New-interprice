import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState('all');
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (token) {
      fetchUserData();
      fetchAccounts();
      fetchAnalytics();
    }
  }, [token]);

  const fetchUserData = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setUser(data);
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/accounts`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setAccounts(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching accounts:', error);
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/analytics/summary`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    window.location.href = '/login';
  };

  if (!token) {
    return <div className="container">Please login first</div>;
  }

  if (loading) {
    return <div className="container">Loading...</div>;
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <h1>🎯 Interprice Dashboard</h1>
          <div className="user-info">
            <span>{user?.username}</span>
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        </div>
      </header>

      {/* Summary Cards */}
      <div className="container">
        <section className="summary-section">
          <div className="card stats-card">
            <h3>📊 Total Followers</h3>
            <p className="stat-number">{analytics?.total_followers || 0}</p>
          </div>
          <div className="card stats-card">
            <h3>📝 Total Posts</h3>
            <p className="stat-number">{analytics?.total_posts || 0}</p>
          </div>
          <div className="card stats-card">
            <h3>❤️ Total Engagement</h3>
            <p className="stat-number">{analytics?.total_engagement || 0}</p>
          </div>
          <div className="card stats-card">
            <h3>🔗 Connected Accounts</h3>
            <p className="stat-number">{analytics?.total_accounts || 0}</p>
          </div>
        </section>

        {/* Platform Breakdown */}
        <section className="platforms-section">
          <h2>📱 Platform Breakdown</h2>
          <div className="platforms-grid">
            {Object.entries(analytics?.platforms || {}).map(([platform, data]) => (
              <div key={platform} className="card platform-card">
                <h3 className="platform-name">{platform.toUpperCase()}</h3>
                <div className="platform-stats">
                  <p>Accounts: <strong>{data.accounts}</strong></p>
                  <p>Followers: <strong>{data.followers}</strong></p>
                  <p>Posts: <strong>{data.posts}</strong></p>
                  <p>Engagement: <strong>{data.engagement}</strong></p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Connected Accounts */}
        <section className="accounts-section">
          <h2>🔗 Connected Accounts</h2>
          <div className="accounts-list">
            {accounts.length > 0 ? (
              accounts.map((account) => (
                <div key={account.id} className="card account-card">
                  <div className="account-header">
                    <h3>{account.platform}</h3>
                    <span className={`status ${account.is_active ? 'active' : 'inactive'}`}>
                      {account.is_active ? '✓ Active' : '✗ Inactive'}
                    </span>
                  </div>
                  <p><strong>Username:</strong> {account.account_username}</p>
                  <p><strong>Followers:</strong> {account.followers_count}</p>
                  <p><strong>Posts:</strong> {account.posts_count}</p>
                  <p><strong>Engagement Rate:</strong> {account.engagement_rate}%</p>
                  <p><strong>Last Scraped:</strong> {account.last_scraped ? new Date(account.last_scraped).toLocaleDateString() : 'Never'}</p>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <p>No accounts connected yet. Add a social media account to get started!</p>
                <button className="btn-primary" onClick={() => window.location.href = '/add-account'}>
                  + Add Account
                </button>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
