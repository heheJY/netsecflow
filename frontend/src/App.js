import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import TrafficOverview from './pages/TrafficOverview';
import AnomalyDetection from './pages/AnomalyDetection';
import DecisionLogs from './pages/DecisionLogs';
import ManualTrafficControl from './pages/ManualTrafficControl';
import Reports from './pages/Reports';
import SystemSettings from './pages/SystemSettings';
import Chatbot from './components/Chatbot';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <Header />
      <div className="main-layout">
        <Sidebar />
        <div className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/traffic-overview" element={<TrafficOverview />} />
            <Route path="/anomaly-detection" element={<AnomalyDetection />} />
            <Route path="/decision-logs" element={<DecisionLogs />} />
            <Route path="/manual-traffic-control" element={<ManualTrafficControl />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/system-settings" element={<SystemSettings />} />
          </Routes>
        </div>
      </div>
      <Chatbot />
    </div>
  );
}

export default App;
