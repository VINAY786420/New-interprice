import React, { useState } from "react";
import { useQuery } from "react-query";
import {
  Search, TrendingUp, Users, DollarSign, ShoppingBag,
  BarChart3, Activity, Globe, MessageSquare, Video,
  Instagram, Linkedin, Facebook, Twitter, Youtube,
  ArrowUpRight, ArrowDownRight, Filter, Download
} from "lucide-react";
import { api } from "../utils/api";

const platformIcons = {
  twitter: Twitter,
  instagram: Instagram,
  reddit: MessageSquare,
  youtube: Video,
  linkedin: Linkedin,
  facebook: Facebook,
  pinterest: Globe,
  google_search: Search,
  amazon: ShoppingBag,
  flipkart: ShoppingBag,
};

const platformColors = {
  twitter: "bg-sky-500",
  instagram: "bg-pink-500",
  reddit: "bg-orange-600",
  youtube: "bg-red-600",
  linkedin: "bg-blue-700",
  facebook: "bg-blue-600",
  pinterest: "bg-red-700",
  google_search: "bg-green-600",
  amazon: "bg-orange-500",
  flipkart: "bg-blue-500",
};

const StatCard = ({ title, value, change, icon: Icon, color }) => (
  <div className="card">
    <div className="flex items-center justify-between mb-4">
      <div className={`p-3 rounded-xl ${color} bg-opacity-10`}>
        <Icon className={`w-6 h-6 ${color.replace("bg-", "text-")}`} />
      </div>
      {change !== undefined && (
        <div className={`flex items-center gap-1 text-sm font-medium ${
          change >= 0 ? "text-success-600" : "text-danger-600"
        }`}>
          {change >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
          {Math.abs(change)}%
        </div>
      )}
    </div>
    <p className="text-gray-500 text-sm">{title}</p>
    <p className="text-2xl font-bold text-gray-900">{value}</p>
  </div>
);

const PlatformCard = ({ platform, stats }) => {
  const Icon = platformIcons[platform] || Globe;
  const color = platformColors[platform] || "bg-gray-500";
  
  return (
    <div className="card hover:shadow-md transition-shadow cursor-pointer group">
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center text-white shadow-lg`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 capitalize group-hover:text-primary-600 transition-colors">
            {platform.replace("_", " ")}
          </h3>
          <p className="text-sm text-gray-500">{stats?.records || 0} records</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-50 rounded-lg p-2">
          <p className="text-xs text-gray-500">Scraped Today</p>
          <p className="font-semibold text-gray-900">{stats?.today || 0}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-2">
          <p className="text-xs text-gray-500">Success Rate</p>
          <p className="font-semibold text-success-600">{stats?.success_rate || "95%"}</p>
        </div>
      </div>
    </div>
  );
};

const RecentDataTable = ({ data }) => (
  <div className="card overflow-hidden">
    <div className="flex items-center justify-between mb-4">
      <h3 className="font-semibold text-gray-900">Recently Scraped Data</h3>
      <button className="btn-secondary text-sm py-1.5 px-3">
        <Download className="w-4 h-4" /> Export
      </button>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left text-xs font-medium text-gray-500 uppercase py-3 px-2">Platform</th>
            <th className="text-left text-xs font-medium text-gray-500 uppercase py-3 px-2">Content</th>
            <th className="text-left text-xs font-medium text-gray-500 uppercase py-3 px-2">Username</th>
            <th className="text-left text-xs font-medium text-gray-500 uppercase py-3 px-2">Engagement</th>
            <th className="text-left text-xs font-medium text-gray-500 uppercase py-3 px-2">Date</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((item, idx) => (
            <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
              <td className="py-3 px-2">
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                  platformColors[item.platform] ? platformColors[item.platform].replace("bg-", "bg-opacity-10 text-") : "bg-gray-100 text-gray-700"
                }`}>
                  {item.platform}
                </span>
              </td>
              <td className="py-3 px-2 max-w-xs">
                <p className="text-sm text-gray-900 truncate">{item.post_content || item.title || "N/A"}</p>
              </td>
              <td className="py-3 px-2 text-sm text-gray-600">{item.username || "N/A"}</td>
              <td className="py-3 px-2">
                <div className="flex items-center gap-3 text-sm text-gray-500">
                  {item.likes_count > 0 && <span>👍 {item.likes_count}</span>}
                  {item.comments_count > 0 && <span>💬 {item.comments_count}</span>}
                  {item.shares_count > 0 && <span>🔄 {item.shares_count}</span>}
                  {item.price && <span className="font-medium text-primary-600">₹{item.price.toLocaleString()}</span>}
                </div>
              </td>
              <td className="py-3 px-2 text-sm text-gray-500">
                {item.posted_at ? new Date(item.posted_at).toLocaleDateString() : "N/A"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

const Dashboard = () => {
  const [timeRange, setTimeRange] = useState("7d");
  
  // Mock data - replace with actual API calls
  const stats = {
    totalRecords: 15420,
    activeScrapers: 10,
    apiRequests: 89340,
    revenue: 45200,
  };
  
  const platformStats = {
    twitter: { records: 3200, today: 145, success_rate: "92%" },
    instagram: { records: 2800, today: 120, success_rate: "88%" },
    reddit: { records: 4100, today: 200, success_rate: "97%" },
    youtube: { records: 1900, today: 85, success_rate: "90%" },
    linkedin: { records: 800, today: 30, success_rate: "75%" },
    facebook: { records: 1200, today: 60, success_rate: "85%" },
    pinterest: { records: 600, today: 25, success_rate: "93%" },
    google_search: { records: 2500, today: 110, success_rate: "96%" },
    amazon: { records: 1800, today: 95, success_rate: "89%" },
    flipkart: { records: 1520, today: 80, success_rate: "87%" },
  };
  
  const recentData = [
    { platform: "amazon", title: "iPhone 15 Pro Max 256GB", username: "Amazon India", price: 159900, likes_count: 0, comments_count: 0, posted_at: "2024-01-15" },
    { platform: "flipkart", title: "Samsung Galaxy S24 Ultra", username: "Flipkart", price: 129999, likes_count: 0, comments_count: 0, posted_at: "2024-01-15" },
    { platform: "reddit", post_content: "Best laptop for programming under 50k?", username: "techie_india", likes_count: 234, comments_count: 56, posted_at: "2024-01-15" },
    { platform: "twitter", post_content: "Just launched my new SaaS product! 🚀", username: "startup_guy", likes_count: 1200, comments_count: 89, shares_count: 45, posted_at: "2024-01-14" },
    { platform: "youtube", post_content: "Complete Python Tutorial 2024", username: "CodeWithHarry", likes_count: 45000, comments_count: 1200, posted_at: "2024-01-14" },
    { platform: "instagram", post_content: "New collection launch! 💃", username: "nykaa", likes_count: 8900, comments_count: 234, posted_at: "2024-01-13" },
  ];
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-gray-500 mt-1">Overview of all scraped data across platforms</p>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="input-field w-36"
              >
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
              </select>
              <button className="btn-primary">
                <Activity className="w-4 h-4" /> Live Monitor
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Records"
            value={stats.totalRecords.toLocaleString()}
            change={12.5}
            icon={BarChart3}
            color="bg-primary-500"
          />
          <StatCard
            title="Active Scrapers"
            value={stats.activeScrapers}
            change={2}
            icon={Globe}
            color="bg-success-500"
          />
          <StatCard
            title="API Requests"
            value={stats.apiRequests.toLocaleString()}
            change={8.3}
            icon={Activity}
            color="bg-warning-500"
          />
          <StatCard
            title="Revenue"
            value={`₹${stats.revenue.toLocaleString()}`}
            change={15.2}
            icon={DollarSign}
            color="bg-danger-500"
          />
        </div>
        
        {/* Platform Cards */}
        <div>
          <h2 className="text-lg font-bold text-gray-900 mb-4">Platform Status</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {Object.entries(platformStats).map(([platform, stats]) => (
              <PlatformCard key={platform} platform={platform} stats={stats} />
            ))}
          </div>
        </div>
        
        {/* Recent Data */}
        <RecentDataTable data={recentData} />
        
        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Data Collection Trend</h3>
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center text-gray-400">
              <BarChart3 className="w-12 h-12" />
              <span className="ml-2">Chart Component</span>
            </div>
          </div>
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Platform Distribution</h3>
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center text-gray-400">
              <Activity className="w-12 h-12" />
              <span className="ml-2">Pie Chart Component</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
