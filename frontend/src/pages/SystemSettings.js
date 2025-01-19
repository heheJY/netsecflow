import React, { useState, useEffect } from 'react';
import './SystemSettings.css';
import axios from 'axios';

function SystemSettings() {
  const [mode, setMode] = useState('balanced'); // Default mode is balanced
  const [sdnControllerIp, setSdnControllerIp] = useState('');
  const [elkIp, setElkIp] = useState('');
  const [honeypotIp, setHoneypotIp] = useState('');

  // Fetch existing settings from backend on load
  useEffect(() => {
    axios.get('http://localhost:5000/api/get-settings')
      .then(response => {
        const settings = response.data.data;
        setMode(settings['Mode'] || 'balanced');
        setSdnControllerIp(settings['SDN Controller IP'] || '');
        setElkIp(settings['ELK IP Address'] || '');
        setHoneypotIp(settings['Honeypot IP Address'] || '');
      })
      .catch(error => console.error('Error fetching settings:', error));
  }, []);

  const handleSaveSettings = () => {
    const settings = {
      "Mode": mode,
      "SDN Controller IP": sdnControllerIp,
      "ELK IP Address": elkIp,
      "Honeypot IP Address": honeypotIp
    };

    // Send settings to backend
    axios.post('http://localhost:5000/api/save-settings', settings)
      .then(response => {
        alert(response.data.message);
      })
      .catch(error => {
        console.error('Error saving settings:', error);
        alert('Failed to save settings');
      });
  };

  const modeDescriptions = {
    strict: 'Strict: High sensitivity, low thresholds for quick detection.',
    balanced: 'Balanced: Moderate sensitivity and thresholds for balanced performance.',
    loose: 'Loose: Low sensitivity, high thresholds to minimize false positives.',
  };

  return (
    <div className="system-settings">
      <h2>System Settings</h2>

      <div className="settings-group">
        <h3>Detection Mode</h3>
        <p>Select a detection mode based on your system requirements:</p>

        {['strict', 'balanced', 'loose'].map((option) => (
          <div key={option}>
            <input
              type="radio"
              id={option}
              name="mode"
              value={option}
              checked={mode === option}
              onChange={(e) => setMode(e.target.value)}
            />
            <label htmlFor={option}>{option.charAt(0).toUpperCase() + option.slice(1)}</label>
          </div>
        ))}
        <p><strong>Description:</strong> {modeDescriptions[mode]}</p>
      </div>

      <div className="settings-group">
        <h3>Application Variables</h3>

        {[
          { label: 'SDN Controller IP', value: sdnControllerIp, set: setSdnControllerIp },
          { label: 'SIEM IP Address', value: elkIp, set: setElkIp },
          { label: 'Honeypot IP Address', value: honeypotIp, set: setHoneypotIp },
        ].map(({ label, value, set }) => (
          <div className="form-field" key={label}>
            <label htmlFor={label}>{label}:</label>
            <input
              type="text"
              id={label}
              value={value}
              onChange={(e) => set(e.target.value)}
              placeholder={`Enter ${label}`}
            />
          </div>
        ))}
      </div>

      <button onClick={handleSaveSettings}>
        Save Settings
      </button>
    </div>
  );
}

export default SystemSettings;
