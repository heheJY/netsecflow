// AnomalyDetection.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AnomalyDetection.css'

function AnomalyDetection() {
  const [anomalies, setAnomalies] = useState([]);
  const [showBlockModal, setShowBlockModal] = useState(false);
  const [blockIp, setBlockIp] = useState('');
  const [showHoneypotModal, setShowHoneypotModal] = useState(false);
  const [redirectIp, setRedirectIp] = useState('');
  const [showIgnoreModal, setShowIgnoreModal] = useState(false);
  const [ignoreIp, setIgnoreIp] = useState('');
  const [flowDetails, setFlowDetails] = useState([]);
  const [selectedIp, setSelectedIp] = useState('');
  const [showFlowModal, setShowFlowModal] = useState(false);

  // Fetch anomalies from the backend on component mount
  useEffect(() => {
    axios.get('http://localhost:5000/api/get-anomalies')
      .then((response) => {
        setAnomalies(response.data.data);
      })
      .catch((error) => console.error('Error fetching anomalies:', error));
  }, []);
  const handleIgnoreSubmit = () => {
    axios.post('http://localhost:5000/api/ignore', { srcIp: ignoreIp })
      .then((response) => {
        alert(response.data.message);
        setShowIgnoreModal(false);
        setIgnoreIp('');
        // Refresh the anomalies table after ignoring an event
        axios.get('http://localhost:5000/api/get-anomalies')
          .then((response) => setAnomalies(response.data.data))
          .catch((error) => console.error('Error fetching anomalies:', error));
      })
      .catch((error) => {
        console.error('Error ignoring event:', error);
        alert('Failed to ignore the event');
      });
  };

  const handleBlockIpSubmit = () => {
    axios.post('http://localhost:5000/api/block', { srcIp: blockIp })
      .then((response) => {
        alert(response.data.message);
        setShowBlockModal(false);
        setBlockIp('');
      })
      .catch((error) => {
        console.error('Error blocking IP:', error);
        alert('Failed to block IP');
      });
  };

  const handleRedirectToHoneypot = () => {
    axios.post('http://localhost:5000/api/redirectHoney', { srcIp: redirectIp })
      .then((response) => {
        alert(response.data.message);
        setShowHoneypotModal(false);
        setRedirectIp('');
      })
      .catch((error) => {
        console.error('Error redirecting to honeypot:', error);
        alert('Failed to redirect to honeypot');
      });
  };

  const fetchFlowDetails = (ip) => {
    axios
      .post("http://localhost:5000/api/get-documents-by-ip", { ip_address: ip })
      .then((response) => {
        const rawData = response.data.data; // Contains all logs
        const consolidatedDetails = [];
  
        for (const [indexName, logs] of Object.entries(rawData)) {
          logs.forEach((log) => {
            if (
              log.client?.ip === ip ||
              log.server?.ip === ip ||
              log.host?.ip?.includes(ip) ||
              log.client_ip === ip
            ) {
              let detail = {
                timestamp: log["@timestamp"] || "-",
                source_ip: ip,
                log_type: indexName,
              };
  
              // Populate fields based on index type
              if (indexName.includes("ad-logs")) {
                detail = {
                  ...detail,
                  description: log.event?.action || log.event?.original || "No description",
                  destination_ip: "N/A",
                  protocol: "N/A",
                  bytes: "N/A",
                  packets: "N/A",
                };
              } else if (indexName.includes("dns-logs")) {
                detail = {
                  ...detail,
                  description: log.question_name || log.message || "No description",
                  destination_ip: "N/A",
                  protocol: log.protocol || "N/A",
                  bytes: "N/A",
                  packets: "N/A",
                };
              } else if (indexName.includes("elastiflow")) {
                detail = {
                  ...detail,
                  description: log.message || "No description",
                  destination_ip: log.destination?.ip || "No destination IP",
                  protocol: log.network?.transport || "No protocol",
                  bytes: log.network?.bytes || "No data transferred",
                  packets: log.network?.packets || "No packets",
                };
              }
  
              consolidatedDetails.push(detail);
            }
          });
        }
  
        setFlowDetails(consolidatedDetails);
        setSelectedIp(ip);
        setShowFlowModal(true);
      })
      .catch((error) => {
        console.error("Error fetching flow details:", error);
        alert("Failed to retrieve flow details.");
      });
  };
  
  return (
    <div className="anomaly-detection">
      <h2>Anomaly Detection</h2>
      <div className="anomaly-list">
        <h3>Recent Anomalies</h3>
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Source IP</th>
              <th>Anomaly Type</th>
              <th>Score</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {anomalies.map((anomaly, index) => (
              <tr key={index}>
                <td>{anomaly.timestamp}</td>
                <td>{anomaly.source_ip}</td>
                <td>{anomaly.event}</td>
                <td>{anomaly.score}</td>
                <td>
                <button onClick={() => fetchFlowDetails(anomaly.source_ip)}>Investigate</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="alerts-panel">
        <h3>Alert Actions</h3>
        <button onClick={() => setShowBlockModal(true)}>Block Traffic</button>
        <button onClick={() => setShowHoneypotModal(true)}>Send to Honeypot</button>
        <button onClick={() => setShowIgnoreModal(true)}>Ignore</button>
      </div>

      {showBlockModal && (
        <div className="modal">
          <div className="modal-content">
            <h3>Block Traffic</h3>
            <label htmlFor="block-ip">Enter Source IP to Block:</label>
            <input
              type="text"
              id="block-ip"
              value={blockIp}
              onChange={(e) => setBlockIp(e.target.value)}
              placeholder="e.g., 192.168.1.10"
            />
            <div className="modal-actions">
              <button onClick={handleBlockIpSubmit}>Submit</button>
              <button onClick={() => setShowBlockModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {showIgnoreModal && (
        <div className="modal">
          <div className="modal-content">
            <h3>Ignore Event</h3>
            <label htmlFor="ignore-ip">Enter Source IP to Ignore:</label>
            <input
              type="text"
              id="ignore-ip"
              value={ignoreIp}
              onChange={(e) => setIgnoreIp(e.target.value)}
              placeholder="e.g., 192.168.1.10"
            />
            <div className="modal-actions">
              <button onClick={handleIgnoreSubmit}>Submit</button>
              <button onClick={() => setShowIgnoreModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {showHoneypotModal && (
        <div className="modal">
          <div className="modal-content">
            <h3>Send to Honeypot</h3>
            <label htmlFor="redirect-ip">Enter Source IP to Redirect:</label>
            <input
              type="text"
              id="redirect-ip"
              value={redirectIp}
              onChange={(e) => setRedirectIp(e.target.value)}
              placeholder="e.g., 192.168.1.10"
            />
            <div className="modal-actions">
              <button onClick={handleRedirectToHoneypot}>Submit</button>
              <button onClick={() => setShowHoneypotModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
      {showFlowModal && (
        <div className="modal">
          <div className="modal-content">
            <h3>Flow Details for IP: {selectedIp}</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Source IP</th>
                    <th>Log Type</th>
                    <th>Description</th>
                    <th>Destination IP</th>
                    <th>Protocol</th>
                    <th>Bytes</th>
                    <th>Packets</th>
                  </tr>
                </thead>
                <tbody>
                  {flowDetails.length > 0 ? (
                    flowDetails.map((detail, index) => (
                      <tr key={index}>
                        <td>{detail.timestamp}</td>
                        <td>{detail.source_ip}</td>
                        <td>{detail.log_type}</td>
                        <td>{detail.description}</td>
                        <td>{detail.destination_ip}</td>
                        <td>{detail.protocol}</td>
                        <td>{detail.bytes}</td>
                        <td>{detail.packets}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="8">No flow details available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <button onClick={() => setShowFlowModal(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AnomalyDetection;
