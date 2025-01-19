import React, { useState, useEffect } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Dashboard.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function Dashboard() {
  const [trafficData, setTrafficData] = useState([]);
  const [recentActions, setRecentActions] = useState([]);
  const [serviceStatus, setServiceStatus] = useState({}); 
  const navigate = useNavigate(); // React Router hook for navigation

  useEffect(() => {
    // Fetch traffic data
    axios.get('http://localhost:5000/api/get-flows')
      .then((response) => setTrafficData(response.data.data))
      .catch((error) => console.error('Error fetching traffic data:', error));

    // Fetch recent actions
    axios.get('http://localhost:5000/api/get-actions')
      .then((response) => setRecentActions(response.data.data))
      .catch((error) => console.error('Error fetching recent actions:', error));

    axios.get('http://localhost:5000/api/service-status')
      .then((response) => setServiceStatus(response.data.data))
      .catch((error) => console.error('Error fetching service statuses:', error));
  }, []);

  // Prepare data for Live Traffic Overview
  const trafficChartData = {
    labels: trafficData.map((flow, index) => `Flow ${index + 1}`),
    datasets: [{
      label: 'Bandwidth (Mbps)',
      data: trafficData.map((flow) => flow.bandwidth),
      borderColor: 'rgba(75, 192, 192, 1)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      tension: 0.3,
      fill: true,
    }]
  };

  // Prepare data for Recent Actions
  const actionCounts = recentActions.reduce((acc, action) => {
    acc[action.action_type] = (acc[action.action_type] || 0) + 1;
    return acc;
  }, {});

  const actionsChartData = {
    labels: Object.keys(actionCounts),
    datasets: [{
      label: 'Actions Count',
      data: Object.values(actionCounts),
      backgroundColor: ['#36A2EB', '#FF6384', '#FFCE56', '#4BC0C0', '#9966FF'],
    }]
  };
    // Service status indicators
  const renderServiceStatus = () => {
    return Object.entries(serviceStatus).map(([service, status]) => (
       <div key={service} className="service-status-card">
        <span className={`status-indicator ${status === 'UP' ? 'up' : 'down'}`}></span>
        <p>{service}</p>
        <p className="status-text">{status}</p>
       </div>
     ));
  };

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <div className="dashboard-widgets">
        <div className="widget" onClick={() => navigate('/traffic-overview')}>
          <h3>Live Traffic Overview</h3>
          <Line data={trafficChartData} options={{ maintainAspectRatio: false }} />
        </div>
        <div className="widget" onClick={() => navigate('/decision-logs')}>
          <h3>Recent Actions</h3>
          <Bar data={actionsChartData} options={{ maintainAspectRatio: false }} />
        </div>
      </div>
      <div className="system-health">
        <h3>System Health</h3>
        <div className="service-status">
          {renderServiceStatus()}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
