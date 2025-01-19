// DecisionLogs.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function DecisionLogs() {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [actionTypeFilter, setActionTypeFilter] = useState('all');
  const [adminTypeFilter, setAdminTypeFilter] = useState('all');

  // Fetch logs from the backend on component mount
  useEffect(() => {
    axios.get('http://localhost:5000/api/get-actions')
      .then((response) => {
        setLogs(response.data.data);
        setFilteredLogs(response.data.data); // Initialize filtered logs
      })
      .catch((error) => console.error('Error fetching logs:', error));
  }, []);

  // Filter logs whenever filters change
  useEffect(() => {
    const applyFilters = () => {
      let filtered = logs;

      if (actionTypeFilter !== 'all') {
        filtered = filtered.filter(log => log.action_type.toLowerCase() === actionTypeFilter);
      }

      if (adminTypeFilter !== 'all') {
        filtered = filtered.filter(log => log.admin_or_automated.toLowerCase() === adminTypeFilter);
      }

      setFilteredLogs(filtered);
    };

    applyFilters();
  }, [actionTypeFilter, adminTypeFilter, logs]);

  return (
    <div className="decision-logs">
      <h2>Decision Logs</h2>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Action Type</th>
            <th>Reason</th>
            <th>Source IP</th>
            <th>Admin/Automated</th>
          </tr>
        </thead>
        <tbody>
          {filteredLogs.map((log, index) => (
            <tr key={index}>
              <td>{log.timestamp}</td>
              <td>{log.action_type}</td>
              <td>{log.reason}</td>
              <td>{log.source_ip}</td>
              <td>{log.admin_or_automated}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="filter-section">
        <h3>Filter Logs</h3>
        <label htmlFor="log-type">Action Type: </label>
        <select
          id="log-type"
          value={actionTypeFilter}
          onChange={(e) => setActionTypeFilter(e.target.value)}
        >
          <option value="all">All</option>
          <option value="block">Block</option>
          <option value="rate-limit">Rate Limit</option>
          <option value="redirect">Honeypot Redirect</option>
        </select>

        <label htmlFor="admin-type">Admin/Automated: </label>
        <select
          id="admin-type"
          value={adminTypeFilter}
          onChange={(e) => setAdminTypeFilter(e.target.value)}
        >
          <option value="all">All</option>
          <option value="admin">Admin</option>
          <option value="automated">Automated</option>
        </select>
      </div>
    </div>
  );
}

export default DecisionLogs;
